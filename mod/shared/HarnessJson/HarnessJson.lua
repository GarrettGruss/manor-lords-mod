-- HarnessJson: a small JSON encoder for harness mods (encode only).
-- Why: UE4SS has no JSON library for plain mods. Harness files must be valid JSON for Python to read.
-- Rules:
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

return M
