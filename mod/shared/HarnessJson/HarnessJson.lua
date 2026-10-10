-- HarnessJson: a small JSON encoder and a strict decoder for harness mods.
-- Why: UE4SS has no JSON library for plain mods. Harness files must be valid JSON for Python to read.
-- The decoder only reads data. It never runs text as code.
-- Encoder rules:
--   nil, NaN and infinity become null.
--   A table with keys 1..n only is an array. Any other table is an object with sorted keys (stable output).
--   An empty table is an empty array. Use HarnessJson.object({}) when an empty object is wanted.

local M = {}

local OBJECT_MARK = {}

-- A Lua table cannot hold nil, so a key with a nil value would vanish from the output.
-- Use HarnessJson.null when the file must show an explicit null.
M.null = setmetatable({}, { __tostring = function() return "null" end })

-- Mark a table so that it is encoded as an object even when it is empty.
function M.object(t)
    return setmetatable(t or {}, { __jsonobject = OBJECT_MARK })
end

local ESCAPES = {
    ['"'] = '\\"',
    ['\\'] = '\\\\',
    ['\n'] = '\\n',
    ['\r'] = '\\r',
    ['\t'] = '\\t',
}

local function encodeString(text)
    text = text:gsub('[%c"\\]', function(c)
        return ESCAPES[c] or string.format("\\u%04x", c:byte())
    end)
    return '"' .. text .. '"'
end

local function encodeNumber(n)
    if n ~= n or n == math.huge or n == -math.huge then return "null" end
    if n == math.floor(n) and math.abs(n) < 1e15 then return string.format("%d", n) end
    return string.format("%.6g", n)
end

local function isArray(t)
    local mt = getmetatable(t)
    if mt and mt.__jsonobject == OBJECT_MARK then return false end
    local count = 0
    for _ in pairs(t) do count = count + 1 end
    for i = 1, count do
        if t[i] == nil then return false end
    end
    return true
end

local encodeValue

local function encodeArray(t)
    local parts = {}
    for i = 1, #t do parts[i] = encodeValue(t[i]) end
    return "[" .. table.concat(parts, ",") .. "]"
end

local function encodeObject(t)
    local keys = {}
    for k in pairs(t) do keys[#keys + 1] = tostring(k) end
    table.sort(keys)
    local parts = {}
    for _, k in ipairs(keys) do
        local v = t[k]
        if v == nil then v = t[tonumber(k)] end
        parts[#parts + 1] = encodeString(k) .. ":" .. encodeValue(v)
    end
    return "{" .. table.concat(parts, ",") .. "}"
end

function encodeValue(value)
    local kind = type(value)
    if kind == "nil" or value == M.null then return "null" end
    if kind == "boolean" then return tostring(value) end
    if kind == "number" then return encodeNumber(value) end
    if kind == "string" then return encodeString(value) end
    if kind == "table" then
        if isArray(value) then return encodeArray(value) end
        return encodeObject(value)
    end
    -- Functions, userdata and threads cannot be stored. Fail loudly so the caller sees the bug.
    error("HarnessJson cannot encode a value of type " .. kind)
end

function M.encode(value)
    return encodeValue(value)
end

---------------------------------------------------------------------------------------------
-- Decoder (strict: it refuses anything that is not plain JSON)
---------------------------------------------------------------------------------------------

local MAX_DEPTH = 6
local MAX_TEXT_CHARS = 16384
local STRING_ESCAPES = { ['"'] = '"', ['\\'] = '\\', ['/'] = '/', b = "\b", f = "\f", n = "\n", r = "\r", t = "\t" }

local function fail(text, position, reason)
    error({ json_error = "bad JSON at character " .. position .. ": " .. reason }, 0)
end

local function skipSpace(text, position)
    return text:find("[^ \t\r\n]", position) or (#text + 1)
end

local function decodeString(text, position)
    local parts = {}
    local index = position + 1
    while true do
        local stop = text:find('["\\%c]', index)
        if not stop then fail(text, position, "string is not closed") end
        parts[#parts + 1] = text:sub(index, stop - 1)
        local mark = text:sub(stop, stop)
        if mark == '"' then return table.concat(parts), stop + 1 end
        if mark ~= "\\" then fail(text, stop, "control character in string") end
        local code = text:sub(stop + 1, stop + 1)
        if code == "u" then
            local hex = text:match("^%x%x%x%x", stop + 2)
            if not hex then fail(text, stop, "bad unicode escape") end
            parts[#parts + 1] = utf8.char(tonumber(hex, 16))
            index = stop + 6
        elseif STRING_ESCAPES[code] then
            parts[#parts + 1] = STRING_ESCAPES[code]
            index = stop + 2
        else
            fail(text, stop, "unknown escape")
        end
    end
end

local function decodeNumber(text, position)
    local literal = text:match("^-?%d+", position)
    if not literal or literal:find("^-?0%d") then fail(text, position, "bad number") end
    local fraction = text:match("^%.%d+", position + #literal) or ""
    local exponent = text:match("^[eE][+-]?%d+", position + #literal + #fraction) or ""
    local whole = literal .. fraction .. exponent
    return tonumber(whole), position + #whole
end

local decodeValue

local function decodeArray(text, position, depth)
    local list = {}
    position = skipSpace(text, position + 1)
    if text:sub(position, position) == "]" then return list, position + 1 end
    while true do
        local item
        item, position = decodeValue(text, position, depth + 1)
        list[#list + 1] = item
        position = skipSpace(text, position)
        local mark = text:sub(position, position)
        if mark == "]" then return list, position + 1 end
        if mark ~= "," then fail(text, position, "expected , or ]") end
        position = skipSpace(text, position + 1)
    end
end

local function decodeObject(text, position, depth)
    local result = M.object({})
    position = skipSpace(text, position + 1)
    if text:sub(position, position) == "}" then return result, position + 1 end
    while true do
        if text:sub(position, position) ~= '"' then fail(text, position, "expected a key") end
        local key
        key, position = decodeString(text, position)
        position = skipSpace(text, position)
        if text:sub(position, position) ~= ":" then fail(text, position, "expected :") end
        if result[key] ~= nil then fail(text, position, "duplicate key " .. key) end
        result[key], position = decodeValue(text, skipSpace(text, position + 1), depth + 1)
        position = skipSpace(text, position)
        local mark = text:sub(position, position)
        if mark == "}" then return result, position + 1 end
        if mark ~= "," then fail(text, position, "expected , or }") end
        position = skipSpace(text, position + 1)
    end
end

local LITERALS = { { "true", true }, { "false", false } }

function decodeValue(text, position, depth)
    if depth > MAX_DEPTH then fail(text, position, "nesting is too deep") end
    local mark = text:sub(position, position)
    if mark == "{" then return decodeObject(text, position, depth) end
    if mark == "[" then return decodeArray(text, position, depth) end
    if mark == '"' then return decodeString(text, position) end
    if mark == "-" or mark:find("%d") then return decodeNumber(text, position) end
    for _, literal in ipairs(LITERALS) do
        if text:sub(position, position + #literal[1] - 1) == literal[1] then return literal[2], position + #literal[1] end
    end
    if text:sub(position, position + 3) == "null" then return M.null, position + 4 end
    fail(text, position, "unexpected character")
end

-- True for a table that came from a JSON object (or was made with HarnessJson.object).
function M.isObject(value)
    local mark = type(value) == "table" and getmetatable(value)
    return mark and mark.__jsonobject == OBJECT_MARK or false
end

-- Returns the value, or nil and a message. JSON null becomes HarnessJson.null.
function M.decode(text)
    if type(text) ~= "string" or #text > MAX_TEXT_CHARS then
        return nil, "JSON text must be a string of at most " .. MAX_TEXT_CHARS .. " characters"
    end
    local ok, value, position = pcall(decodeValue, text, skipSpace(text, 1), 1)
    if not ok then
        if type(value) == "table" and value.json_error then return nil, value.json_error end
        error(value, 0)
    end
    if skipSpace(text, position) <= #text then return nil, "bad JSON at character " .. position .. ": text after the value" end
    return value
end

return M
