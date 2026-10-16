-- ModState: keep the values of a mod inside a save (spec 24, option A; mod feature M01).
-- The values live as Names in the `Tags` array of a game object (the player pawn). The game saves and loads that array.
--
-- Entry format: a Name "<mod>:<key>=<value>", for example "invasion:raid_days=412".
-- The version entry is "<mod>:v=<n>".
--
-- Usage (all calls on the game thread):
--   local state = ModState.open("invasion", "pawn", 1)   -- the same state table for the same mod and owner
--   state:register("raid_days", 400, "integer")           -- kinds: integer, number, boolean, string
--   state:get("raid_days"); state:set("raid_days", 399)   -- set flushes at once unless autoflush is off
--
-- Rules:
--   * Only entries with the prefix "<mod>:" are read or written. Other Tags are never touched (A6).
--   * An entry is changed IN PLACE (the array element is overwritten). The module never removes an element,
--     because a removal from Lua is not proven safe. A key has one element for its whole life (no duplicates, A1).
--   * An unregistered key makes get and set fail with a clear message (A5).
--   * An entry with the prefix whose key is not registered is kept as it is and is listed in dump().unknown.
--   * Never write a Tags array through the bridge. It crashes the game. This module writes with FName.

local M = {}

local MOD_PATTERN = "^[a-z][a-z0-9_]*$"
local KEY_PATTERN = "^[a-z][a-z0-9_]*$"
local STRING_PATTERN = "^[A-Za-z0-9_.%-]*$"
local VERSION_KEY = "v"
local MAX_NAME_CHARS = 1023
local KINDS = { integer = true, number = true, boolean = true, string = true }

local states = {} -- cache key -> state, so every feature of a mod shares one state table
local State = {}
State.__index = State

---------------------------------------------------------------------------------------------
-- Values
---------------------------------------------------------------------------------------------

local function fail(message) error("ModState: " .. message, 0) end

local function is_finite(value) return type(value) == "number" and value == value and math.abs(value) ~= math.huge end

local function check_value(kind, value, what)
    if kind == "integer" then
        if not is_finite(value) or value ~= math.floor(value) then fail(what .. " must be an integer, got " .. tostring(value)) end
    elseif kind == "number" then
        if not is_finite(value) then fail(what .. " must be a finite number, got " .. tostring(value)) end
    elseif kind == "boolean" then
        if type(value) ~= "boolean" then fail(what .. " must be a boolean, got " .. tostring(value)) end
    elseif type(value) ~= "string" or not value:match(STRING_PATTERN) then
        fail(what .. " must be a string of A-Z a-z 0-9 _ . -, got " .. tostring(value))
    end
end

local function encode(kind, value)
    if kind == "integer" then return string.format("%d", value) end
    if kind == "number" then return string.format("%.17g", value) end
    return tostring(value)
end

-- Text to value. Returns nil and a reason when the text does not fit the kind.
function M.decode(kind, text)
    if kind == "integer" then
        if not text:match("^%-?%d+$") then return nil, "not an integer: " .. text end
        return math.tointeger(tonumber(text)) or tonumber(text)
    elseif kind == "number" then
        local number = tonumber(text)
        if not is_finite(number) then return nil, "not a number: " .. text end
        return number
    elseif kind == "boolean" then
        if text == "true" then return true end
        if text == "false" then return false end
        return nil, "not a boolean: " .. text
    end
    if not text:match(STRING_PATTERN) then return nil, "not a plain string: " .. text end
    return text
end

---------------------------------------------------------------------------------------------
-- Owner and Tags
---------------------------------------------------------------------------------------------

-- The live player pawn, or nil. It is replaced on each load, so it is looked up on each use.
local function find_pawn()
    local engine = FindFirstOf("RTSMultiEngineCPP")
    if engine == nil or not engine:IsValid() then return nil end
    local pawn = engine.playerRef
    if pawn == nil or not pawn:IsValid() then return nil end
    return pawn
end

function State:owner_object()
    if self.owner == "pawn" then return find_pawn() end
    if self.owner:IsValid() then return self.owner end
    return nil
end

local function require_owner(self)
    local object = self:owner_object()
    if object == nil then fail("the owner of '" .. self.mod .. "' state is not available (no live player pawn)") end
    return object
end

local function tag_text(tags, index) return tags[index]:ToString() end

---------------------------------------------------------------------------------------------
-- State
---------------------------------------------------------------------------------------------

-- Open (or find) the state of `mod` on `owner` ("pawn" by default, or an object that has Tags).
-- `version` is the version this code writes. A load reads the stored version into state.stored_version.
-- When the owner is not available yet, the state stays unloaded. Call state:load() later.
function M.open(mod, owner, version)
    if type(mod) ~= "string" or not mod:match(MOD_PATTERN) then fail("bad mod name " .. tostring(mod) .. " (use a-z 0-9 _)") end
    owner = owner or "pawn"
    if owner ~= "pawn" and (type(owner) ~= "userdata" or not owner:IsValid()) then fail('owner must be "pawn" or a valid object') end
    local cache_key = mod .. "|" .. (owner == "pawn" and "pawn" or owner:GetFullName())
    local state = states[cache_key]
    if state == nil then
        state = setmetatable({
            mod = mod, owner = owner, prefix = mod .. ":", kinds = {}, defaults = {}, values = {}, dirty = {},
            version = version, stored_version = nil, loaded = false, autoflush = true, unknown = {},
        }, State)
        states[cache_key] = state
    else
        if version ~= nil then state.version = version end
        if owner ~= "pawn" then state.owner = owner end
    end
    if state:owner_object() ~= nil then state:load() end
    return state
end

function State:register(key, default, kind)
    if type(key) ~= "string" or not key:match(KEY_PATTERN) or key == VERSION_KEY then
        fail("bad key " .. tostring(key) .. " (use a-z 0-9 _, a letter first, and not '" .. VERSION_KEY .. "')")
    end
    if not KINDS[kind] then fail("key '" .. key .. "' has unknown kind " .. tostring(kind)) end
    if self.kinds[key] then fail("key '" .. key .. "' is registered twice") end
    check_value(kind, default, "default of '" .. key .. "'")
    if #(self.prefix .. key .. "=" .. encode(kind, default)) > MAX_NAME_CHARS then fail("default of '" .. key .. "' is too long") end
    self.kinds[key] = kind
    self.defaults[key] = default
    self.values[key] = default
    if self.loaded then self:load() end
end

function State:check_registered(key)
    if self.kinds[key] == nil then fail("key '" .. tostring(key) .. "' is not registered for mod '" .. self.mod .. "'") end
end

local function require_loaded(self)
    if not self.loaded then fail("state '" .. self.mod .. "' is not loaded yet (no live player pawn)") end
end

-- Read the entries of this mod from the live Tags. A missing entry gives the default (a save from before the mod).
function State:load()
    local tags = require_owner(self).Tags
    local values, seen, unknown, stored_version = {}, {}, {}, nil
    for key, default in pairs(self.defaults) do values[key] = default end
    for index = 1, #tags do
        local name = tag_text(tags, index)
        if name:sub(1, #self.prefix) == self.prefix then
            local key, text = name:sub(#self.prefix + 1):match("^([^=]+)=(.*)$")
            if key == nil then fail("bad entry '" .. name .. "' (expected " .. self.prefix .. "<key>=<value>)") end
            if seen[key] then fail("duplicate entries for '" .. self.prefix .. key .. "' in the Tags") end
            seen[key] = true
            if key == VERSION_KEY then
                stored_version = math.tointeger(tonumber(text)) or fail("bad version entry '" .. name .. "'")
            elseif self.kinds[key] then
                local value, reason = M.decode(self.kinds[key], text)
                if reason then fail("bad entry '" .. name .. "': " .. reason) end
                values[key] = value
            else
                unknown[#unknown + 1] = name
            end
        end
    end
    self.values, self.unknown, self.stored_version, self.loaded, self.dirty = values, unknown, stored_version, true, {}
end

function State:get(key)
    self:check_registered(key)
    require_loaded(self)
    return self.values[key]
end

function State:set(key, value)
    self:check_registered(key)
    require_loaded(self)
    check_value(self.kinds[key], value, "value of '" .. key .. "'")
    if self.values[key] ~= value then
        self.values[key] = value
        self.dirty[key] = true
    end
    if self.autoflush then self:flush() end
end

-- Write one entry. Overwrite the element of the key, or append when the key has no element yet.
local function write_entry(self, tags, key, text)
    local lead = self.prefix .. key .. "="
    local name = lead .. text
    if #name > MAX_NAME_CHARS then fail("entry '" .. name:sub(1, 60) .. "...' is longer than " .. MAX_NAME_CHARS .. " characters") end
    for index = 1, #tags do
        local current = tag_text(tags, index)
        if current:sub(1, #lead) == lead then
            if current ~= name then tags[index] = FName(name) end
            return
        end
    end
    tags[#tags + 1] = FName(name)
end

-- Write the dirty keys, and the version entry when it is missing or different, into the live Tags.
function State:flush()
    require_loaded(self)
    local tags = require_owner(self).Tags
    for key in pairs(self.dirty) do
        write_entry(self, tags, key, encode(self.kinds[key], self.values[key]))
    end
    self.dirty = {}
    if self.version ~= nil and self.stored_version ~= self.version then
        write_entry(self, tags, VERSION_KEY, string.format("%d", self.version))
        self.stored_version = self.version
    end
end

-- A plain table for the harness: the values, the unknown entries of this mod, and all live Tags.
function State:dump()
    local object = self:owner_object()
    local all_tags = {}
    if object ~= nil then
        local tags = object.Tags
        for index = 1, #tags do all_tags[#all_tags + 1] = tag_text(tags, index) end
    end
    local values, kinds = {}, {}
    for key, value in pairs(self.values) do
        values[key] = value
        kinds[key] = self.kinds[key]
    end
    return {
        mod = self.mod, loaded = self.loaded, version = self.version, stored_version = self.stored_version,
        values = values, kinds = kinds, unknown = self.unknown, tags = all_tags,
    }
end

-- For tests: forget all cached states.
function M.reset() states = {} end

return M
