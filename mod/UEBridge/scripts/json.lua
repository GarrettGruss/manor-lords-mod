-- Minimal JSON encode/decode for UEBridge. Pure Lua 5.4, no dependencies.
-- Encodes: nil, boolean, number, string, table (array if keys are 1..n, else object).
-- Non-finite numbers encode as null. Decodes the full JSON grammar including \uXXXX.

local json = {}

local escapes = { ['"'] = '\\"', ['\\'] = '\\\\', ['\b'] = '\\b', ['\f'] = '\\f',
                  ['\n'] = '\\n', ['\r'] = '\\r', ['\t'] = '\\t' }

local function escapeStr(s)
    return '"' .. s:gsub('[%c"\\]', function(c)
        return escapes[c] or string.format('\\u%04x', c:byte())
    end) .. '"'
end

local function isArray(t)
    local n = 0
    for k in pairs(t) do
        if type(k) ~= "number" or k <= 0 or math.floor(k) ~= k then return false end
        n = n + 1
    end
    for i = 1, n do if t[i] == nil then return false end end
    return true, n
end

local function encode(v, seen)
    local tv = type(v)
    if v == nil then return "null" end
    if tv == "boolean" then return v and "true" or "false" end
    if tv == "number" then
        if v ~= v or v == math.huge or v == -math.huge then return "null" end
        if math.type(v) == "integer" then return tostring(v) end
        return string.format("%.17g", v)
    end
    if tv == "string" then return escapeStr(v) end
    if tv == "table" then
        seen = seen or {}
        if seen[v] then return '"<cycle>"' end
        seen[v] = true
        local out = {}
        local arr, n = isArray(v)
        if arr then
            for i = 1, n do out[i] = encode(v[i], seen) end
            seen[v] = nil
            return "[" .. table.concat(out, ",") .. "]"
        end
        local keys = {}
        for k in pairs(v) do keys[#keys + 1] = k end
        table.sort(keys, function(a, b) return tostring(a) < tostring(b) end)
        for _, k in ipairs(keys) do
            out[#out + 1] = escapeStr(tostring(k)) .. ":" .. encode(v[k], seen)
        end
        seen[v] = nil
        return "{" .. table.concat(out, ",") .. "}"
    end
    return escapeStr(tostring(v))
end

function json.encode(v) return encode(v, nil) end

-- Decoder -------------------------------------------------------------------------------

local function decodeError(str, pos, msg)
    error(string.format("json: %s at position %d (%s)", msg, pos, str:sub(pos, pos + 20)), 0)
end

local function skipWs(str, pos)
    return str:find("[^ \t\r\n]", pos) or #str + 1
end

local decodeValue

local simpleEscapes = { b = "\b", f = "\f", n = "\n", r = "\r", t = "\t",
                        ['"'] = '"', ["\\"] = "\\", ["/"] = "/" }

local function decodeString(str, pos)
    local out, i = {}, pos + 1
    while true do
        local c = str:sub(i, i)
        if c == "" then decodeError(str, i, "unterminated string") end
        if c == '"' then return table.concat(out), i + 1 end
        if c == "\\" then
            local e = str:sub(i + 1, i + 1)
            if simpleEscapes[e] then
                out[#out + 1] = simpleEscapes[e]
                i = i + 2
            elseif e == "u" then
                local cp = tonumber(str:sub(i + 2, i + 5), 16)
                if not cp then decodeError(str, i, "bad \\u escape") end
                i = i + 6
                if cp >= 0xD800 and cp <= 0xDBFF and str:sub(i, i + 1) == "\\u" then
                    local lo = tonumber(str:sub(i + 2, i + 5), 16)
                    if lo and lo >= 0xDC00 and lo <= 0xDFFF then
                        cp = 0x10000 + (cp - 0xD800) * 0x400 + (lo - 0xDC00)
                        i = i + 6
                    end
                end
                out[#out + 1] = utf8.char(cp)
            else
                decodeError(str, i, "bad escape")
            end
        else
            local j = str:find('["\\]', i) or (#str + 1)
            out[#out + 1] = str:sub(i, j - 1)
            i = j
        end
    end
end

function decodeValue(str, pos)
    pos = skipWs(str, pos)
    local c = str:sub(pos, pos)
    if c == "{" then
        local obj = {}
        pos = skipWs(str, pos + 1)
        if str:sub(pos, pos) == "}" then return obj, pos + 1 end
        while true do
            pos = skipWs(str, pos)
            if str:sub(pos, pos) ~= '"' then decodeError(str, pos, "expected key") end
            local key; key, pos = decodeString(str, pos)
            pos = skipWs(str, pos)
            if str:sub(pos, pos) ~= ":" then decodeError(str, pos, "expected ':'") end
            local val; val, pos = decodeValue(str, pos + 1)
            obj[key] = val
            pos = skipWs(str, pos)
            local d = str:sub(pos, pos)
            if d == "}" then return obj, pos + 1 end
            if d ~= "," then decodeError(str, pos, "expected ',' or '}'") end
            pos = pos + 1
        end
    elseif c == "[" then
        local arr = {}
        pos = skipWs(str, pos + 1)
        if str:sub(pos, pos) == "]" then return arr, pos + 1 end
        while true do
            local val; val, pos = decodeValue(str, pos)
            arr[#arr + 1] = val
            pos = skipWs(str, pos)
            local d = str:sub(pos, pos)
            if d == "]" then return arr, pos + 1 end
            if d ~= "," then decodeError(str, pos, "expected ',' or ']'") end
            pos = pos + 1
        end
    elseif c == '"' then
        return decodeString(str, pos)
    elseif str:sub(pos, pos + 3) == "true" then return true, pos + 4
    elseif str:sub(pos, pos + 4) == "false" then return false, pos + 5
    elseif str:sub(pos, pos + 3) == "null" then return nil, pos + 4
    else
        local num = str:match("^-?%d+%.?%d*[eE]?[-+]?%d*", pos)
        if not num or num == "" then decodeError(str, pos, "unexpected character") end
        local n = tonumber(num)
        if not n then decodeError(str, pos, "bad number") end
        return n, pos + #num
    end
end

function json.decode(str)
    local v, pos = decodeValue(str, 1)
    pos = skipWs(str, pos)
    if pos <= #str then decodeError(str, pos, "trailing garbage") end
    return v
end

return json
