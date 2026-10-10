-- UEBridge: a file-based request/response channel that lets an external process (the ue4ss-bridge
-- MCP server, or anything that can write a file) run Lua inside a live UE4SS game. Game-agnostic:
-- nothing here names a game or an install path.
--
--   external  ->  writes  <ue4ss>\bridge\request.json    {"id":..,"op":"eval","code":".."}
--   this mod  ->  polls it, runs the code on the game thread, writes response.json
--
-- The poll is a LoopAsync timer, not a per-tick hook, and does work only when the request file
-- exists. All game-object access happens inside ExecuteInGameThread. No sockets, no processes.
--
-- Wire format (protocol 3)
--   request : {"id": string, "op": "hello"|"ping"|"eval"|"batch", "code": string, "calls": [..]}
--   response: {"id", "ok": bool, "result": any, "output": [string], "error": string|null,
--              "ms": n, "protocol": 3}
--
-- Eval snippets run in an environment that inherits _G plus the UEB helper table below and
-- UEHelpers. Whatever the chunk returns is serialised: UObjects become {"__object": fullname,
-- "address": n}, FName / FString become strings, TArrays become lists, structs are walked
-- through their reflected type.

local VERSION = "1.2.1"
local PROTOCOL = 3
local MOD_NAME = "UEBridge"

-- Paths -----------------------------------------------------------------------------------
-- Lua io resolves relative paths against the process working directory (Binaries\Win64, the exe
-- directory), not the ue4ss folder, so the bridge path is built absolute.
local function ue4ssDir()
    local ok, dirs = pcall(IterateGameDirectories)
    local win64 = ok and dirs and dirs.Game and dirs.Game.Binaries and dirs.Game.Binaries.Win64
    if win64 and win64.__absolute_path then
        return win64.__absolute_path .. "\\ue4ss"
    end
    return "ue4ss"
end
local UE4SS_DIR = ue4ssDir()
local MOD_DIR = UE4SS_DIR .. "\\Mods\\" .. MOD_NAME
local MOD_PATH = MOD_DIR .. "\\scripts\\main.lua"

package.path = MOD_DIR .. "\\scripts\\?.lua;" .. package.path
local json = require("json")
local UEHelpers = require("UEHelpers")

local function log(fmt, ...)
    print("[" .. MOD_NAME .. "] " .. string.format(fmt, ...) .. "\n")
end

-- Settings ----------------------------------------------------------------------------------
-- scripts\settings.lua is optional; the keys are documented there.
-- It lives in scripts\ because mod managers that deploy only <mod>\scripts drop a root-level file.
-- scripts\settings.lua wins; a root copy (the 1.0.0 layout) is a fallback only.
local SETTINGS = { enabled = true, poll_ms = 50, allow_eval = true, allow_writes = true, bridge_dir = nil }
local ROOT_SETTINGS_IGNORED = false
do
    local scriptsChunk = loadfile(MOD_DIR .. "\\scripts\\settings.lua")
    local rootChunk = loadfile(MOD_DIR .. "\\settings.lua")
    if scriptsChunk and rootChunk then ROOT_SETTINGS_IGNORED = true end
    local chunk = scriptsChunk or rootChunk
    if chunk then
        local ok, user = pcall(chunk)
        if ok and type(user) == "table" then
            for k, v in pairs(user) do
                if SETTINGS[k] ~= nil or k == "bridge_dir" then SETTINGS[k] = v end
            end
        else
            log("settings.lua did not return a table (%s); using defaults", tostring(user))
        end
    end
end
if ROOT_SETTINGS_IGNORED then
    log("scripts\\settings.lua in use; ignoring %s\\settings.lua (1.0.0 layout, delete it)", MOD_DIR)
end

-- eval can write, so allow_writes = false forces it off; EVAL_FORCED_OFF lets the refusal say so.
local EVAL_FORCED_OFF = false
if not SETTINGS.allow_writes and SETTINGS.allow_eval then
    EVAL_FORCED_OFF = true
    log("allow_writes = false forces allow_eval off (eval can write); structured batch ops still work")
end
if not SETTINGS.allow_writes then SETTINGS.allow_eval = false end

local DIR = SETTINGS.bridge_dir or (UE4SS_DIR .. "\\bridge")
local REQUEST = DIR .. "/request.json"
local RESPONSE = DIR .. "/response.json"
local RESPONSE_TMP = DIR .. "/response.tmp"
local POLL_MS = math.max(50, tonumber(SETTINGS.poll_ms) or 50)

-- One line, rewritten in place and flushed, naming the operation in flight. A native crash cannot
-- be caught by pcall; the server reads this after a timeout to report what was running.
local TRACE = DIR .. "/lastop.log"
local traceHandle, traceOpened = nil, false
local function trace(s)
    if not traceOpened then traceHandle = io.open(TRACE, "wb") traceOpened = true end
    if not traceHandle then return end
    traceHandle:seek("set", 0)
    -- Fixed width so a short line overwrites a longer one. string.rep, since %-300s exceeds
    -- string.format's two-digit width cap.
    local line = tostring(s):sub(1, 300)
    traceHandle:write(line .. string.rep(" ", 300 - #line))
    traceHandle:flush()
end

-- File helpers --------------------------------------------------------------------------

local function readFile(path)
    local f = io.open(path, "rb")
    if not f then return nil end
    local s = f:read("a")
    f:close()
    return s
end

local function writeAtomic(path, tmp, content)
    local f = io.open(tmp, "wb")
    if not f then return false, "cannot open " .. tmp end
    f:write(content)
    f:close()
    os.remove(path)
    local ok, err = os.rename(tmp, path)
    if not ok then return false, tostring(err) end
    return true
end

-- Value serialisation --------------------------------------------------------------------

-- A batched props result nests values two levels deeper than a direct one; 6 keeps them intact.
local MAX_DEPTH = 6
local MAX_ITEMS = 200

local function safe(fn, ...)
    local ok, r = pcall(fn, ...)
    if ok then return r end
    return nil
end

-- ForEachProperty wrapper. UE4SS can pass the callback nil, and an error raised inside the
-- callback escapes as a "[Lua::call_function]" error. Nil entries are skipped and counted; an fn
-- error stops the walk and is re-raised here. fn returning true stops the walk.
-- Returns the number of nil entries skipped.
local function eachProperty(st, fn)
    local skipped, failed, failure = 0, false, nil
    st:ForEachProperty(function(prop)
        if prop == nil then skipped = skipped + 1; return end
        local ok, stop = pcall(fn, prop)
        if not ok then failed, failure = true, stop; return true end
        if stop == true then return true end
    end)
    if failed then error(failure, 0) end
    return skipped
end

local encodeValue

local function encodeUObject(obj)
    local out = { __object = obj:GetFullName() }
    out.address = safe(function() return obj:GetAddress() end)
    return out
end

local function encodeArray(arr, depth)
    local out, n = {}, 0
    local count = safe(function() return arr:GetArrayNum() end) or 0
    arr:ForEach(function(i, elem)
        n = n + 1
        if n > MAX_ITEMS then return true end
        out[n] = encodeValue(safe(function() return elem:get() end), depth + 1)
    end)
    if count > MAX_ITEMS then out[MAX_ITEMS + 1] = string.format("<%d more>", count - MAX_ITEMS) end
    return out
end

local UNSAFE_TYPES = { SoftObjectProperty = true, SoftClassProperty = true }

-- Probe list for a struct whose type does not resolve.
local STRUCT_FIELDS = { "X", "Y", "Z", "W", "Pitch", "Yaw", "Roll", "R", "G", "B", "A",
                        "Min", "Max", "AssetPath", "SubPathString", "PackageName", "AssetName",
                        "TagName", "Value", "Guid", "B", "C", "D", "Key" }

-- A struct value's GetFullName() names its type ("ScriptStruct /Script/CoreUObject.Vector"); that
-- path resolves to a UScriptStruct whose properties walk like a class. Cached per type.
local STRUCT_TYPE_CACHE = {}

local function structType(s)
    local ok, full = pcall(function() return s:GetFullName() end)
    if not ok or type(full) ~= "string" then return nil, nil end
    local path = full:match("^%S+%s+(.+)$") or full
    local hit = STRUCT_TYPE_CACHE[path]
    if hit ~= nil then
        if hit == false then return nil, path end
        return hit, path
    end
    local st = StaticFindObject(path)
    if st and safe(function() return st:IsValid() end) then
        STRUCT_TYPE_CACHE[path] = st
        return st, path
    end
    STRUCT_TYPE_CACHE[path] = false
    return nil, path
end

-- Blueprint UserDefinedStruct fields carry a "_<n>_<32 hex>" suffix. Read by the raw reflected
-- name, report the readable one.
local function fieldName(n)
    local base, _, hex = n:match("^(.-)_(%d+)_(%x+)$")
    if base and #hex == 32 then return base end
    return n
end

local function encodeStruct(s, depth)
    local out = { __struct = true }
    out.address = safe(function() return s:GetStructAddress() end)
    local st, path = structType(s)
    out.__type = path
    if not st then
        out.__fields = "guessed"          -- type did not resolve
        for _, k in ipairs(STRUCT_FIELDS) do
            local v = safe(function() return s[k] end)
            if v ~= nil then out[k] = encodeValue(v, depth + 1) end
        end
        return out
    end
    -- Walk the super chain: FVector_NetQuantize100 declares nothing itself and inherits X/Y/Z.
    local seen, skipped = {}, 0
    while st and st:IsValid() do
        skipped = skipped + eachProperty(st, function(prop)
            local rawn = prop:GetFName():ToString()
            if seen[rawn] then return end
            seen[rawn] = true
            local ptype = safe(function() return prop:GetClass():GetFName():ToString() end)
            local key = fieldName(rawn)
            if UNSAFE_TYPES[ptype] then
                out[key] = "<skipped: " .. tostring(ptype) .. ">"
                return
            end
            local ok, v = pcall(function() return s[rawn] end)
            if ok then
                out[key] = encodeValue(v, depth + 1)
            else
                out[key] = "<error: " .. tostring(v) .. ">"
            end
        end)
        st = safe(function() return st:GetSuperStruct() end)
    end
    if skipped > 0 then out.__skipped = skipped end
    return out
end

function encodeValue(v, depth)
    depth = depth or 0
    local tv = type(v)
    if tv == "nil" or tv == "boolean" or tv == "number" or tv == "string" then return v end
    if depth > MAX_DEPTH then return "<depth>" end
    if tv == "table" then
        local out = {}
        local keys, n = {}, 0
        for k in pairs(v) do n = n + 1; keys[n] = k end
        if n > MAX_ITEMS then
            -- pairs() order is not stable across walks; sort so a truncated walk keeps the same subset.
            table.sort(keys, function(a, b)
                local ta, tb = type(a), type(b)
                if ta ~= tb then return ta < tb end
                if ta == "number" or ta == "string" then return a < b end
                return tostring(a) < tostring(b)
            end)
        end
        for i = 1, math.min(n, MAX_ITEMS) do
            local k = keys[i]
            out[type(k) == "number" and k or tostring(k)] = encodeValue(v[k], depth + 1)
        end
        if n > MAX_ITEMS then out["<more>"] = n - MAX_ITEMS end
        return out
    end
    if tv == "userdata" then
        local kind = safe(function() return v:type() end)
        if kind == "FName" or kind == "FString" or kind == "FText" then
            -- tostring(v) embeds a fresh pointer per walk and would diff as a change.
            return safe(function() return v:ToString() end) or ("<" .. kind .. ">")
        end
        if kind == "TArray" then return encodeArray(v, depth) end
        if kind == "UScriptStruct" then return encodeStruct(v, depth) end
        if kind == "RemoteUnrealParam" or kind == "LocalUnrealParam" then
            return encodeValue(safe(function() return v:get() end), depth)
        end
        if kind == "FWeakObjectPtr" then
            return encodeValue(safe(function() return v:Get() end), depth)
        end
        if v.IsValid and v.GetFullName then
            if not safe(function() return v:IsValid() end) then return { __object = "<invalid>" } end
            return encodeUObject(v)
        end
        return { __type = kind or "userdata", str = tostring(v) }
    end
    return tostring(v)
end

-- Helper library exposed to eval snippets as UEB -------------------------------------------

UEB = {}
UEB.encode = encodeValue
UEB.trace = trace
UEB.version = VERSION
UEB.protocol = PROTOCOL
UEB.settings = SETTINGS

-- Resolve an object reference string:
--   "/Script/Pkg.Object"    full path, via StaticFindObject
--   "first:ClassName"       first live instance of that short class name
--   "cdo:/Script/Pkg.Class" class default object of that class
function UEB.resolve(ref)
    if type(ref) ~= "string" then return ref end
    local first = ref:match("^first:(.+)$")
    if first then
        local o = FindFirstOf(first)
        if o and o:IsValid() then return o end
        error("no live instance of " .. first)
    end
    local cdo = ref:match("^cdo:(.+)$")
    if cdo then
        local cls = StaticFindObject(cdo)
        if not cls or not cls:IsValid() then error("class not found: " .. cdo) end
        return cls:GetCDO()
    end
    local o = StaticFindObject(ref)
    if not o or not o:IsValid() then error("object not found: " .. ref) end
    return o
end

-- Reflected properties of an object as {name, type, value}. includeSuper defaults to false.
-- SoftObject/SoftClass reads are skipped unless readSoft: they have crashed the process inside
-- UE4SS's property reader, which no pcall can catch.
function UEB.props(ref, includeSuper, readSoft, pattern)
    local obj = UEB.resolve(ref)
    if pattern ~= nil then
        -- Validate here so a bad pattern is reported against the argument, not a property.
        local okPat = pcall(string.match, "probe", pattern)
        if not okPat then error("invalid Lua pattern: " .. tostring(pattern)) end
    end
    if includeSuper == nil then includeSuper = false end
    local out, seen, skipped = {}, {}, 0
    local cls = obj:GetClass()
    while cls and cls:IsValid() do
        local cname = safe(function() return cls:GetFName():ToString() end)
        skipped = skipped + eachProperty(cls, function(prop)
            local name = prop:GetFName():ToString()
            if not seen[name] then
                seen[name] = true
                if pattern and not name:match(pattern) then return end
                local ptype = safe(function() return prop:GetClass():GetFName():ToString() end)
                trace("props " .. tostring(cname) .. "." .. name .. " (" .. tostring(ptype) .. ")")
                -- Explicit branches: `ok and x or y` misreports values that encode to false/nil.
                local encoded
                if UNSAFE_TYPES[ptype] and not readSoft then
                    encoded = "<skipped: " .. ptype .. ">"
                else
                    local ok, val = pcall(function() return obj[name] end)
                    if ok then
                        encoded = encodeValue(val, 1)
                    else
                        encoded = "<error: " .. tostring(val) .. ">"
                    end
                end
                out[#out + 1] = { name = name, type = ptype, value = encoded }
            end
        end)
        if not includeSuper then break end
        cls = safe(function() return cls:GetSuperStruct() end)
    end
    local res = { object = obj:GetFullName(), class = obj:GetClass():GetFullName(), properties = out }
    if skipped > 0 then res.skipped = skipped end
    return res
end

-- Snapshots and diffs ---------------------------------------------------------------------
-- A snapshot is one UEB.props walk kept under a label for a later diff. Read-only. Stored on _G
-- so UEB.reload() (dofile) keeps it; keyed by label, not address, since addresses are reused after GC.
UEB_SNAPSHOTS = UEB_SNAPSHOTS or {}

-- Both sides of a diff come out of encodeValue with the same caps, so truncation markers match.
-- Object and struct addresses are the only fields volatile between walks of unchanged state;
-- object references compare by their encoded path.
local function volatileKey(t, k)
    return k == "address" and (t.__object ~= nil or t.__struct ~= nil)
end

local function joinPath(base, k)
    if type(k) == "number" then return base .. "[" .. tostring(k) .. "]" end
    if base == "" then return tostring(k) end
    return base .. "." .. tostring(k)
end

-- Scalars that count as unchanged even though `==` disagrees:
--   NaN, which is never equal to itself;
--   two "<error: ...>" read markers, whose text embeds a fresh pointer on each walk.
local function scalarEqual(a, b)
    if a == b then return true end
    local ta, tb = type(a), type(b)
    if ta ~= tb then return false end
    if ta == "number" then return a ~= a and b ~= b end
    if ta == "string" then return a:sub(1, 7) == "<error:" and b:sub(1, 7) == "<error:" end
    return false
end

local diffValue

-- Appends {path, before, after} rows into out.changed / out.added / out.removed.
diffValue = function(path, before, after, out)
    local tb, ta = type(before), type(after)
    if tb ~= "table" or ta ~= "table" then
        if tb ~= ta or not scalarEqual(before, after) then
            out.changed[#out.changed + 1] = { path = path, before = before, after = after }
        end
        return
    end
    if before.__object ~= nil or after.__object ~= nil then
        if tostring(before.__object) ~= tostring(after.__object) then
            out.changed[#out.changed + 1] = { path = path, before = before.__object, after = after.__object }
        end
        return
    end
    -- Userdata fallback { __type, str }: str embeds a pointer per walk, so compare __type only.
    if before.__type ~= nil and before.str ~= nil and after.__type ~= nil and after.str ~= nil then
        if tostring(before.__type) ~= tostring(after.__type) then
            out.changed[#out.changed + 1] = { path = path, before = before.__type, after = after.__type }
        end
        return
    end
    for k, v in pairs(before) do
        if not volatileKey(before, k) then
            local av = after[k]
            if av == nil then
                out.removed[#out.removed + 1] = { path = joinPath(path, k), before = v }
            else
                diffValue(joinPath(path, k), v, av, out)
            end
        end
    end
    for k, v in pairs(after) do
        if not volatileKey(after, k) and before[k] == nil then
            out.added[#out.added + 1] = { path = joinPath(path, k), after = v }
        end
    end
end

-- The walk as {name -> {type, value}}, which is what a diff indexes.
local function propIndex(walk)
    local m, n = {}, 0
    for _, p in ipairs(walk.properties or {}) do
        m[p.name] = { type = p.type, value = p.value }
        n = n + 1
    end
    return m, n
end

local function requireSnapshot(label)
    if type(label) ~= "string" or label == "" then error("a snapshot label (a non-empty string) is required") end
    local snap = UEB_SNAPSHOTS[label]
    if snap then return snap end
    local known = {}
    for k in pairs(UEB_SNAPSHOTS) do known[#known + 1] = k end
    table.sort(known)
    error("no snapshot labelled '" .. label .. "'; known: "
          .. (#known > 0 and table.concat(known, ", ") or "<none>"))
end

-- An existing label is replaced.
function UEB.snapshot(ref, label, includeSuper, pattern)
    if type(label) ~= "string" or label == "" then error("snapshot needs a label (a non-empty string)") end
    if includeSuper == nil then includeSuper = false end
    local walk = UEB.props(ref, includeSuper, false, pattern)
    local props, count = propIndex(walk)
    local taken = os.time()   -- wall clock, whole seconds since the epoch
    UEB_SNAPSHOTS[label] = {
        label = label, path = walk.object, class = walk.class, taken = taken, count = count,
        options = { ref = ref, include_super = includeSuper, pattern = pattern },
        props = props,
    }
    return { label = label, path = walk.object, count = count, taken = taken }
end

-- Diff results skip the batch re-encode (PREENCODED_OPS); cap the row lists here so they always
-- serialise as JSON lists.
local MAX_DIFF_ROWS = 500

local function capRows(out)
    local dropped = nil
    for _, key in ipairs({ "changed", "added", "removed" }) do
        local rows = out[key]
        if #rows > MAX_DIFF_ROWS then
            dropped = dropped or {}
            dropped[key] = #rows - MAX_DIFF_ROWS
            for i = #rows, MAX_DIFF_ROWS + 1, -1 do rows[i] = nil end
        end
    end
    out.truncated = dropped
end

-- Re-walks with the snapshot's options. ref = nil uses the snapshot's reference.
function UEB.diff(ref, label, update)
    local snap = requireSnapshot(label)
    local opts = snap.options
    if ref == nil then ref = opts.ref end
    local walk = UEB.props(ref, opts.include_super, false, opts.pattern)
    local props, count = propIndex(walk)

    local out = { label = label, path = walk.object, changed = {}, added = {}, removed = {}, same = 0 }
    if walk.object ~= snap.path then
        out.stored_path = snap.path
        out.path_changed = true
    end
    for name, old in pairs(snap.props) do
        local new = props[name]
        if new == nil then
            out.removed[#out.removed + 1] = { path = name, before = old.value }
        else
            local before = #out.changed + #out.added + #out.removed
            diffValue(name, old.value, new.value, out)
            if #out.changed + #out.added + #out.removed == before then out.same = out.same + 1 end
        end
    end
    for name, new in pairs(props) do
        if snap.props[name] == nil then
            out.added[#out.added + 1] = { path = name, after = new.value }
        end
    end

    if update then
        snap.props, snap.count, snap.path, snap.class = props, count, walk.object, walk.class
        snap.taken = os.time()
        out.updated = true
    end
    capRows(out)
    return out
end

function UEB.snapshots()
    local out = {}
    for label, snap in pairs(UEB_SNAPSHOTS) do
        out[#out + 1] = { label = label, path = snap.path, taken = snap.taken, count = snap.count }
    end
    table.sort(out, function(a, b) return a.label < b.label end)
    return out
end

function UEB.forget(label)
    if type(label) ~= "string" or label == "" then error("forget needs a label, or \"*\" for all") end
    if label == "*" then
        local n = 0
        for k in pairs(UEB_SNAPSHOTS) do UEB_SNAPSHOTS[k] = nil; n = n + 1 end
        return { forgotten = n }
    end
    requireSnapshot(label)
    UEB_SNAPSHOTS[label] = nil
    return { forgotten = 1, label = label }
end

-- Reflected UFunctions on the object's class chain.
function UEB.funcs(ref)
    local obj = UEB.resolve(ref)
    local out, seen = {}, {}
    local cls = obj:GetClass()
    while cls and cls:IsValid() do
        cls:ForEachFunction(function(fn)
            local name = fn:GetFName():ToString()
            if not seen[name] then
                seen[name] = true
                out[#out + 1] = { name = name, owner = cls:GetFName():ToString(),
                                  flags = safe(function() return fn:GetFunctionFlags() end) }
            end
        end)
        cls = safe(function() return cls:GetSuperStruct() end)
    end
    return out
end

-- UE4SS returns an "<invalid>" object for an undeclared property name and silently ignores writes
-- to one, so get/set check the reflection first. Returns found, nil entries skipped.
local function declaresProperty(cls, name)
    local skipped = 0
    while cls and cls:IsValid() do
        local found = false
        skipped = skipped + eachProperty(cls, function(prop)
            if prop:GetFName():ToString() == name then found = true; return true end
        end)
        if found then return true, skipped end
        cls = safe(function() return cls:GetSuperStruct() end)
    end
    return false, skipped
end

local function declaresFunction(cls, name)
    while cls and cls:IsValid() do
        local found = false
        cls:ForEachFunction(function(fn)
            if fn:GetFName():ToString() == name then found = true end
        end)
        if found then return true end
        cls = safe(function() return cls:GetSuperStruct() end)
    end
    return false
end

local function requireProperty(obj, name)
    local cls = obj:GetClass()
    local found, skipped = declaresProperty(cls, name)
    if found then return end
    local cname = tostring(safe(function() return cls:GetFName():ToString() end))
    if declaresFunction(cls, name) then
        error("'" .. name .. "' is a UFunction on " .. cname .. ", not a property; call it with call_function")
    end
    if skipped > 0 then
        error("no readable property '" .. name .. "' on " .. cname .. ": UE4SS returned " .. skipped
              .. " unreadable property entries for the class, which can mean the object is being torn"
              .. " down; resolve it again and retry")
    end
    error("no property '" .. name .. "' on " .. cname .. "; inspect_object lists the ones it has")
end

local function requireWrites(what)
    if not SETTINGS.allow_writes then
        error(what .. " refused: allow_writes = false in " .. MOD_NAME .. "/scripts/settings.lua")
    end
end

function UEB.get(ref, prop)
    local obj = UEB.resolve(ref)
    requireProperty(obj, prop)
    return obj[prop]
end

-- Returns { previous, current }; previous is what a caller restores from.
function UEB.set(ref, prop, value)
    requireWrites("set")
    local obj = UEB.resolve(ref)
    requireProperty(obj, prop)
    local okPrev, prev = pcall(function() return obj[prop] end)
    local out = {}
    if okPrev then
        out.previous = encodeValue(prev, 1)
    else
        out.previous = "<unreadable: " .. tostring(prev) .. ">"
    end
    obj[prop] = value
    out.current = encodeValue(obj[prop], 1)
    return out
end

function UEB.call(ref, fname, args)
    requireWrites("call")
    local obj = UEB.resolve(ref)
    local fn = obj[fname]
    if fn == nil then error("no function " .. fname .. " on " .. obj:GetFullName()) end
    return fn(obj, table.unpack(args or {}))
end

-- Live instances of a short class name.
function UEB.objects(className, limit)
    limit = limit or 100
    local found = FindAllOf(className) or {}
    local out = {}
    for i, o in ipairs(found) do
        if i > limit then out[#out + 1] = string.format("<%d more>", #found - limit); break end
        out[#out + 1] = o:GetFullName()
    end
    return { count = #found, objects = out }
end

-- Loaded reflected types (Class, BlueprintGeneratedClass, ScriptStruct, Enum) matching a pattern.
function UEB.types(pattern, limit)
    limit = limit or 200
    local out, total = {}, 0
    ForEachUObject(function(obj)
        if not obj:IsValid() then return end
        local cls = obj:GetClass()
        if not cls or not cls:IsValid() then return end
        local cn = cls:GetFName():ToString()
        if cn == "Class" or cn == "BlueprintGeneratedClass" or cn == "ScriptStruct" or cn == "Enum" then
            local n = obj:GetFName():ToString()
            if not pattern or n:find(pattern) then
                total = total + 1
                if total <= limit then out[total] = { name = n, kind = cn, path = obj:GetFullName() } end
            end
        end
    end)
    return { count = total, types = out }
end

-- Subclasses -------------------------------------------------------------------------------
-- Every loaded class derived from a base class. The engine has no reverse index, so this walks
-- GUObjectArray once testing IsChildOf: about 1.5 s on a large game.
function UEB.subclasses(ref, limit, pattern)
    limit = tonumber(limit) or 200
    local base = UEB.resolve(ref)
    local baseKind = safe(function() return base:GetClass():GetFName():ToString() end)
    if baseKind ~= "Class" and baseKind ~= "BlueprintGeneratedClass" then
        error("not a class: " .. tostring(safe(function() return base:GetFullName() end))
              .. " is a " .. tostring(baseKind)
              .. "; pass a class path such as /Script/Engine.PlayerController")
    end
    if pattern ~= nil then
        -- Validate here so a bad pattern is reported against the argument, not a class name.
        local okPat = pcall(string.match, "probe", pattern)
        if not okPat then error("invalid Lua pattern: " .. tostring(pattern)) end
    end
    local baseAddr = safe(function() return base:GetAddress() end)
    local basePath = safe(function() return base:GetFullName() end)
    local rows = {}
    trace("subclasses " .. tostring(basePath))
    ForEachUObject(function(obj)
        if not obj:IsValid() then return end
        local cls = obj:GetClass()
        if not cls or not cls:IsValid() then return end
        local cn = cls:GetFName():ToString()
        if cn ~= "Class" and cn ~= "BlueprintGeneratedClass" then return end
        -- Exclude the base itself; addresses are the only identity a class object has here.
        if safe(function() return obj:GetAddress() end) == baseAddr then return end
        if not safe(function() return obj:IsChildOf(base) end) then return end
        local n = obj:GetFName():ToString()
        if pattern and not n:find(pattern) then return end
        rows[#rows + 1] = {
            name = n, kind = cn, path = obj:GetFullName(),
            parent = safe(function() return obj:GetSuperStruct():GetFName():ToString() end),
        }
    end)
    -- GUObjectArray order is allocation order, which changes between runs; sort for stable output.
    table.sort(rows, function(a, b) return a.path < b.path end)
    local total = #rows
    for i = total, limit + 1, -1 do rows[i] = nil end
    return { base = basePath, count = total, types = rows }
end

-- What the player is looking at ---------------------------------------------------------------
-- A line trace from the camera (or from an actor's own location and forward vector). Read-only:
-- it calls only const engine getters and the trace itself.

local function traceObject(v)
    if v == nil then return nil end
    local kind = safe(function() return v:type() end)
    if kind == "RemoteUnrealParam" or kind == "LocalUnrealParam" then v = safe(function() return v:get() end) end
    if kind == "FWeakObjectPtr" then v = safe(function() return v:Get() end) end
    if v ~= nil and safe(function() return v:IsValid() end) then return v end
    return nil
end

local function objName(o) if o then return safe(function() return o:GetFullName() end) end end
local function objClass(o) if o then return safe(function() return o:GetClass():GetFName():ToString() end) end end

local MAX_TRACE_MATERIALS = 32

function UEB.target(distance, channel, ref)
    distance = tonumber(distance) or 5000
    channel = tonumber(channel) or 0
    local startV, fwd
    -- Each engine call gets its own trace line: a native crash cannot be caught by pcall, so the
    -- last line written names the stage that killed the process.
    if ref ~= nil and ref ~= "" then
        trace("target: resolve " .. tostring(ref))
        local actor = UEB.resolve(ref)
        trace("target: K2_GetActorLocation")
        local loc = actor:K2_GetActorLocation()
        trace("target: GetActorForwardVector")
        fwd = actor:GetActorForwardVector()
        startV = { X = loc.X, Y = loc.Y, Z = loc.Z }
    else
        trace("target: PlayerController")
        local pc = FindFirstOf("PlayerController")
        if not pc or not pc:IsValid() then error("no live PlayerController to trace from") end
        local cam = pc.PlayerCameraManager
        if not cam or not cam:IsValid() then error("the player controller has no PlayerCameraManager") end
        trace("target: GetCameraLocation")
        local loc = cam:GetCameraLocation()
        trace("target: GetCameraRotation")
        local rot = cam:GetCameraRotation()
        trace("target: GetForwardVector")
        fwd = UEHelpers.GetKismetMathLibrary():GetForwardVector(rot)
        startV = { X = loc.X, Y = loc.Y, Z = loc.Z }
    end
    local endV = { X = startV.X + fwd.X * distance,
                   Y = startV.Y + fwd.Y * distance,
                   Z = startV.Z + fwd.Z * distance }
    trace("target: GetWorld")
    local world = UEHelpers.GetWorld()
    if not world or not world:IsValid() then error("no world to trace in") end
    local ksl = UEHelpers.GetKismetSystemLibrary()
    if not ksl or not ksl:IsValid() then error("KismetSystemLibrary not available") end
    -- LineTraceSingle fills `hit` as an out parameter; it comes back as a plain Lua table.
    local hit = {}
    trace("target: LineTraceSingle")
    local okTrace, err = pcall(function()
        return ksl:LineTraceSingle(world, startV, endV, channel, false, {}, 0, hit, true, {}, {}, 1.0)
    end)
    if not okTrace then error("LineTraceSingle failed: " .. tostring(err)) end
    trace("target: encode")

    local out = { hit = hit.bBlockingHit and true or false }
    if not out.hit then return out end
    local comp = traceObject(hit.Component)
    local actor = comp and traceObject(safe(function() return comp:GetOwner() end)) or nil
    out.actor = objName(actor)
    out.actor_class = objClass(actor)
    out.component = objName(comp)
    out.component_class = objClass(comp)
    out.distance = hit.Distance
    out.impact_point = encodeValue(hit.ImpactPoint, 1)
    out.impact_normal = encodeValue(hit.ImpactNormal, 1)
    out.bone = encodeValue(hit.BoneName, 1)
    out.phys_material = objName(traceObject(hit.PhysMaterial))
    if comp and safe(function() return comp.GetMaterials end) ~= nil then
        trace("target: GetMaterials")
        local okM, arr = pcall(function() return comp:GetMaterials() end)
        if okM and arr ~= nil then
            local enc = safe(function() return encodeValue(arr, 1) end)
            if type(enc) == "table" then
                local mats = {}
                for i = 1, math.min(#enc, MAX_TRACE_MATERIALS) do
                    local e = enc[i]
                    mats[i] = (type(e) == "table" and e.__object) or e
                end
                out.materials = mats
            end
        end
    end
    return out
end

-- Event streams ------------------------------------------------------------------------------
-- A watch samples properties on a timer; a hook fires on a UFunction call. Both append to one
-- shared ring buffer that the server drains with the `events` op. Stored on _G so UEB.reload()
-- (a dofile of this file) keeps running streams and their backlog, as UEB_SNAPSHOTS does.
UEB_STREAMS = UEB_STREAMS or {}
UEB_EVENTS = UEB_EVENTS or { rows = {}, seq = 0, first = 1, dropped = 0 }

local MAX_EVENTS = 2000
local MIN_WATCH_MS = 100         -- a pass that has to look its object up costs an object scan
                                 -- (10-25 ms) on the game thread, which also runs the Lua state

-- Rows are keyed by seq rather than pushed onto a list, so eviction is O(1) and a client can ask
-- for everything after a seq it already has.
local function pushEvent(row)
    local buf = UEB_EVENTS
    buf.seq = buf.seq + 1
    row.seq = buf.seq
    row.t = os.clock()
    buf.rows[buf.seq] = row
    local evict = buf.seq - MAX_EVENTS
    if evict >= buf.first then
        for s = buf.first, evict do buf.rows[s] = nil end
        buf.dropped = buf.dropped + (evict - buf.first + 1)
        buf.first = evict + 1
    end
    local rec = UEB_STREAMS[row.label]
    if rec then rec.events = (rec.events or 0) + 1 end
    return row
end

local function newStream(label, kind, rec)
    if type(label) ~= "string" or label == "" then error("a stream label (a non-empty string) is required") end
    if UEB_STREAMS[label] then
        error("a stream labelled '" .. label .. "' is already running; stop it first with unwatch")
    end
    rec.label, rec.kind = label, kind
    rec.events, rec.started, rec.active = 0, os.time(), true
    UEB_STREAMS[label] = rec
    return rec
end

-- Sample properties on a timer and append an event on change (every = true: on every sample).
-- names is one name or a list.
-- The game-thread runner is built once: the LoopAsync body allocates nothing, because allocating
-- on the mod's async thread while the game thread runs Lua in the same state corrupts that state
-- (a 50 ms watch crashed a game in lua_next).
-- The object is held between passes and rechecked with IsValid(). A lookup, a full object scan on
-- the game thread, happens only when the object is gone, a read faulted, or the watch is lost.
-- A reference that stops resolving records one "lost" row and retries about once a second.
-- Adopting a different object (by address and full name) records a "resumed" row with the new
-- path and resets the baseline. The same object back after a blip records nothing; a UObject
-- without GetAddress always counts as different. Only unwatch stops a watch.
function UEB.watch(ref, names, label, interval_ms, every)
    if type(names) == "string" then names = { names } end
    if type(names) ~= "table" or #names == 0 then error("watch needs a property name, or a list of names") end
    local interval = math.max(MIN_WATCH_MS, tonumber(interval_ms) or 250)
    -- Resolve once here so a bad reference fails the call rather than the loop.
    local probe = UEB.resolve(ref)
    local rec = newStream(label, "watch", {
        ref = ref, names = names, interval_ms = interval, every = every and true or false,
        last = {}, seen = {}, busy = false, lost = false, skip = 0,
        obj = probe,
        addr = safe(function() return probe:GetAddress() end),
        path = safe(function() return probe:GetFullName() end),
    })
    -- While lost, retry about once a second instead of every interval. Computed once: the timer
    -- body only decrements it, so it never allocates.
    local lostSkip = math.max(1, math.ceil(1000 / interval)) - 1

    -- Game thread. Allocation here is fine; on the timer thread it is not.
    local function doSample()
        local obj = rec.obj
        if obj ~= nil then
            local okV, isValid = pcall(function() return obj:IsValid() end)
            if not (okV and isValid == true) then obj, rec.obj = nil, nil end
        end
        -- A lookup is a 10 to 25 ms object scan on the game thread, so only when nothing valid is
        -- cached. A respawn shows as IsValid() false; a stale object that faults raises into the
        -- per-name pcall below, which drops the cache.
        if obj == nil then
            local okR, fresh = pcall(UEB.resolve, rec.ref)
            if okR and fresh ~= nil then
                local freshAddr = safe(function() return fresh:GetAddress() end)
                local freshPath = safe(function() return fresh:GetFullName() end)
                if not rec.lost and freshAddr ~= nil and freshAddr == rec.addr
                        and freshPath ~= nil and freshPath == rec.path then
                    -- Same object back after a blip or read fault: keep the baseline, no row.
                    -- Address alone is not identity: UE reuses object slots and a respawn can land
                    -- in the freed one.
                    obj, rec.obj = fresh, fresh
                else
                    -- A different object (respawn, or recovery from lost). Reset the baseline so its
                    -- first sample is not reported as a change.
                    obj, rec.obj = fresh, fresh
                    rec.last, rec.seen = {}, {}
                    rec.lost, rec.skip = false, 0
                    rec.addr = freshAddr
                    rec.path = freshPath
                    pushEvent({ label = label, kind = "stream", event = "resumed", path = rec.path })
                end
            else
                -- Usually a map transition. Report once, keep the stream, retry slowly.
                if not rec.lost then
                    rec.lost = true
                    pushEvent({ label = label, kind = "stream", event = "lost",
                                error = okR and "the reference no longer resolves"
                                             or tostring(fresh) })
                end
                rec.skip = lostSkip
                return
            end
        end
        for _, name in ipairs(rec.names) do
            local okv, enc = pcall(function() return encodeValue(obj[name], 1) end)
            if not okv then enc = "<error: " .. tostring(enc) .. ">" end
            local prev, had = rec.last[name], rec.seen[name]
            local changed = false
            if had then
                local d = { changed = {}, added = {}, removed = {} }
                diffValue(name, prev, enc, d)
                changed = (#d.changed + #d.added + #d.removed) > 0
            end
            if rec.every or (had and changed) then
                -- Assigned explicitly: `had and prev or nil` drops a boolean false before-value.
                local row = { label = label, kind = "watch", path = name, after = enc }
                if had then row.before = prev end
                pushEvent(row)
            end
            rec.last[name], rec.seen[name] = enc, true
            if not okv then
                -- Drop the faulting object and skip the remaining names; the next pass resolves first.
                rec.obj = nil
                break
            end
        end
    end

    local function sample()
        local ok, err = pcall(doSample)
        -- Clear busy first: a throw in the concat or in trace must not wedge the timer.
        rec.busy = false
        if not ok then pcall(trace, "watch " .. label .. ": " .. tostring(err)) end
    end

    LoopAsync(interval, function()
        if not rec.active or UEB_STREAMS[label] ~= rec then return true end
        -- One sample in flight at a time: a slow game thread must not queue overlapping closures.
        if rec.busy then return false end
        if rec.skip > 0 then rec.skip = rec.skip - 1 return false end
        rec.busy = true
        ExecuteInGameThread(sample)
        return false
    end)
    return { label = label, kind = "watch", path = rec.path, names = names,
             interval_ms = interval, every = rec.every }
end

-- Record every call of a UFunction. The callback copies parameters and nothing else: calling any
-- UFunction from inside a hook, or touching the hooked object beyond its name, crashes the game.
function UEB.hook(path, label, max_args)
    requireWrites("hook")
    if type(path) ~= "string" or path == "" then
        error("hook needs a function path such as /Script/Engine.PlayerController:ClientRestart")
    end
    local maxArgs = tonumber(max_args) or 8
    local short = path:match("[%.:]([%w_]+)$") or path
    local rec = newStream(label, "hook", { fn = path, max_args = maxArgs })
    local callback = function(ctx, ...)
        local params = table.pack(...)
        -- Nothing in here may error: an error inside a hook callback unwinds through native code.
        pcall(function()
            local args = {}
            for i = 1, math.min(params.n, maxArgs) do
                local okA, v = pcall(function() return encodeValue(params[i]:get(), 1) end)
                args[i] = okA and v or "<unreadable>"
            end
            local okS, selfName = pcall(function() return ctx:get():GetFullName() end)
            pushEvent({ label = label, kind = "hook", fn = short,
                        self = okS and selfName or nil, args = args })
        end)
    end
    local okReg, pre, post = pcall(RegisterHook, path, callback)
    if not okReg then
        UEB_STREAMS[label] = nil
        error("RegisterHook failed for " .. path .. ": " .. tostring(pre))
    end
    rec.pre, rec.post = pre, post
    return { label = label, kind = "hook", fn = path, pre = pre, post = post, max_args = maxArgs }
end

-- Drain the buffer. since is a seq, exclusive; next is the highest seq scanned, to pass back.
function UEB.events(since, label, limit, clear)
    local buf = UEB_EVENTS
    since = tonumber(since) or 0
    limit = tonumber(limit) or 500
    local from = math.max(since + 1, buf.first)
    local out, last = {}, since
    for s = from, buf.seq do
        local row = buf.rows[s]
        if row and (label == nil or row.label == label) then
            if #out >= limit then break end
            out[#out + 1] = row
        end
        last = s
    end
    if clear then
        if label ~= nil then
            -- Only the returned rows; other labels keep their backlog.
            for _, row in ipairs(out) do buf.rows[row.seq] = nil end
            while buf.first <= buf.seq and buf.rows[buf.first] == nil do buf.first = buf.first + 1 end
        elseif last >= buf.first then
            for s = buf.first, last do buf.rows[s] = nil end
            buf.first = last + 1
        end
    end
    local buffered = 0
    for s = buf.first, buf.seq do if buf.rows[s] then buffered = buffered + 1 end end
    return { events = out, next = last, dropped = buf.dropped, buffered = buffered }
end

function UEB.streams()
    local out = {}
    for label, rec in pairs(UEB_STREAMS) do
        local target
        if rec.kind == "hook" then
            target = rec.fn
        else
            target = tostring(rec.ref) .. " " .. table.concat(rec.names or {}, ",")
        end
        out[#out + 1] = { label = label, kind = rec.kind, target = target,
                          interval_ms = rec.interval_ms, events = rec.events or 0,
                          started = rec.started, active = rec.active and true or false,
                          lost = rec.lost and true or false }
    end
    table.sort(out, function(a, b) return a.label < b.label end)
    return out
end

function UEB.unwatch(label)
    if type(label) ~= "string" or label == "" then error("unwatch needs a label, or \"*\" for all") end
    local function stop(l, rec)
        rec.active = false
        UEB_STREAMS[l] = nil
        if rec.kind == "hook" and rec.pre ~= nil then
            pcall(UnregisterHook, rec.fn, rec.pre, rec.post)
        end
    end
    if label == "*" then
        local n = 0
        for l, rec in pairs(UEB_STREAMS) do stop(l, rec); n = n + 1 end
        return { stopped = n }
    end
    local rec = UEB_STREAMS[label]
    if not rec then
        local known = {}
        for k in pairs(UEB_STREAMS) do known[#known + 1] = k end
        table.sort(known)
        error("no stream labelled '" .. label .. "'; running: "
              .. (#known > 0 and table.concat(known, ", ") or "<none>"))
    end
    stop(label, rec)
    return { stopped = 1, label = label }
end

function UEB.console(cmd)
    requireWrites("console")
    local pc = UEHelpers.GetPlayerController()
    local world = UEHelpers.GetWorld()
    local ksl = UEHelpers.GetKismetSystemLibrary()
    if ksl and ksl:IsValid() and world and world:IsValid() then
        ksl:ExecuteConsoleCommand(world, cmd, pc)
        return "executed via KismetSystemLibrary"
    end
    if pc and pc:IsValid() then
        pc:ConsoleCommand(cmd, false)
        return "executed via PlayerController"
    end
    error("no world or player controller to run a console command in")
end

function UEB.world()
    local pc = FindFirstOf("PlayerController")
    local out = {}
    if pc and pc:IsValid() then
        out.playerController = pc:GetFullName()
        local pawn = safe(function() return pc.Pawn end)
        out.pawn = (pawn and pawn:IsValid()) and pawn:GetFullName() or nil
        local world = safe(function() return pc:GetWorld() end)
        out.world = (world and world:IsValid()) and world:GetFullName() or nil
    end
    local gi = safe(function() return UEHelpers.GetGameInstance() end)
    out.gameInstance = (gi and gi:IsValid()) and gi:GetFullName() or nil
    local gm = safe(function() return UEHelpers.GetGameModeBase() end)
    out.gameMode = (gm and gm:IsValid()) and gm:GetFullName() or nil
    return out
end

-- Handshake: version, protocol and the settings in effect.
function UEB.hello()
    return {
        mod = MOD_NAME, version = VERSION, protocol = PROTOCOL,
        poll_ms = POLL_MS, allow_eval = SETTINGS.allow_eval, allow_writes = SETTINGS.allow_writes,
        bridge_dir = DIR, ue4ss_dir = UE4SS_DIR,
    }
end

local dumpers = {
    usmap = function() DumpUSMAP(true) end,
    jmap = function() DumpJMAP(true) end,
    uht = function() GenerateUHTCompatibleHeaders() end,
    cxx = function() GenerateSDK() end,
    actors = function() DumpAllActors() end,
    objects = function() DumpAllObjects() end,
    static_meshes = function() DumpStaticMeshes() end,
}

function UEB.dump(kind)
    local fn = dumpers[kind]
    if not fn then error("unknown dump kind " .. tostring(kind)) end
    fn()
    return "dump " .. kind .. " written to the ue4ss directory"
end

-- Results that skip the batch re-encode: already encoded (props, the snapshot ops) or plain
-- scalars in plain tables (funcs, objects, types). Re-encoding would re-apply MAX_DEPTH and turn
-- a list longer than MAX_ITEMS into an object keyed "1".."200".
local PREENCODED_OPS = { props = true, funcs = true, objects = true, types = true,
                         snapshot = true, diff = true, snapshots = true, forget = true,
                         subclasses = true, target = true, watch = true, hook = true,
                         events = true, streams = true, unwatch = true }

-- Several ops in one round trip, each pcall-fenced. Also the structured surface that stays
-- available when allow_eval is off.
local BATCH_OPS = {
    hello   = function(a) return UEB.hello() end,
    -- Read-only: the recovery path when allow_eval is off. UEB.reload() runs dofile on the game
    -- thread this handler is already on; UEB.hello() is looked up after it so the reply carries
    -- the new settings.
    reload  = function(a)
        local msg = UEB.reload()
        local info = UEB.hello()
        info.reloaded = true
        info.generation = UEB_GENERATION
        info.message = msg
        return info
    end,
    world   = function(a) return UEB.world() end,
    get     = function(a) return UEB.get(a.ref, a.name) end,
    set     = function(a) return UEB.set(a.ref, a.name, a.value) end,
    call    = function(a) return UEB.call(a.ref, a["function"], a.args) end,
    props   = function(a) return UEB.props(a.ref, a.include_super, a.read_soft, a.pattern) end,
    funcs   = function(a) return UEB.funcs(a.ref) end,
    snapshot  = function(a) return UEB.snapshot(a.ref, a.label, a.include_super, a.pattern) end,
    diff      = function(a) return UEB.diff(a.ref, a.label, a.update) end,
    snapshots = function(a) return UEB.snapshots() end,
    forget    = function(a) return UEB.forget(a.label) end,
    objects = function(a) return UEB.objects(a.class_name, a.limit) end,
    types   = function(a) return UEB.types(a.pattern, a.limit) end,
    subclasses = function(a) return UEB.subclasses(a.ref, a.limit, a.pattern) end,
    target     = function(a) return UEB.target(a.distance, a.channel, a.ref) end,
    watch      = function(a) return UEB.watch(a.ref, a.names or a.name, a.label, a.interval_ms, a.every) end,
    hook       = function(a) return UEB.hook(a["function"], a.label, a.max_args) end,
    events     = function(a) return UEB.events(a.since, a.label, a.limit, a.clear) end,
    streams    = function(a) return UEB.streams() end,
    unwatch    = function(a) return UEB.unwatch(a.label) end,
    console = function(a) return UEB.console(a.command) end,
    dump    = function(a) return UEB.dump(a.kind) end,
    find    = function(a)
        local o = UEB.resolve(a.ref)
        return { object = o:GetFullName(), class = o:GetClass():GetFullName(), address = o:GetAddress() }
    end,
}

function UEB.batch(calls)
    if type(calls) ~= "table" then error("batch expects a list of calls") end
    local out = {}
    for i, c in ipairs(calls) do
        local op = tostring(c and c.op)
        local fn = BATCH_OPS[op]
        if not fn then
            local known = {}
            for k in pairs(BATCH_OPS) do known[#known + 1] = k end
            table.sort(known)
            out[i] = { op = op, ok = false, error = "unknown batch op '" .. op .. "'; known: " .. table.concat(known, ", ") }
        else
            trace("batch[" .. i .. "] " .. op)
            local ok, res = pcall(fn, c)
            if ok then
                out[i] = { op = op, ok = true, result = PREENCODED_OPS[op] and res or encodeValue(res, 1) }
            else out[i] = { op = op, ok = false, error = tostring(res) } end
        end
    end
    return out
end

-- Request handling -----------------------------------------------------------------------

local function runEval(code)
    local output = {}
    local env = setmetatable({
        -- UEHelpers is a file local here, so an eval chunk cannot reach it through _G.
        UEHelpers = UEHelpers,
        print = function(...)
            local parts = {}
            for i = 1, select("#", ...) do parts[i] = tostring((select(i, ...))) end
            output[#output + 1] = table.concat(parts, "\t")
        end,
    }, { __index = _G })
    local chunk, err = load(code, "=bridge", "t", env)
    if not chunk then return false, nil, output, "compile: " .. tostring(err) end
    local ok, result = xpcall(chunk, function(e) return tostring(e) .. "\n" .. debug.traceback() end)
    if not ok then return false, nil, output, result end
    local okEnc, encoded = pcall(encodeValue, result, 0)
    if not okEnc then return true, tostring(result), output, "encode: " .. tostring(encoded) end
    return true, encoded, output, nil
end

local busy = false
local handled = 0

-- ms is os.clock() CPU time, an approximation; Lua has no wall clock finer than a second.
local function respond(id, ok, result, output, err, started)
    local body = json.encode({
        id = id, ok = ok, result = result, output = output, error = err,
        ms = math.floor((os.clock() - started) * 1000), protocol = PROTOCOL,
    })
    local wrote, werr = writeAtomic(RESPONSE, RESPONSE_TMP, body)
    if not wrote then log("response write failed: %s", tostring(werr)) end
end

local function handle(req)
    local started = os.clock()
    handled = handled + 1
    if req.op == "ping" then
        respond(req.id, true, { pong = true, handled = handled, poll_ms = POLL_MS }, {}, nil, started)
        return
    end
    if req.op == "hello" then
        local info = UEB.hello()
        info.handled = handled
        respond(req.id, true, info, {}, nil, started)
        return
    end
    if req.op == "batch" then
        if type(req.calls) ~= "table" then
            respond(req.id, false, nil, {}, "batch needs a 'calls' list", started)
            return
        end
        busy = true
        trace("batch id=" .. tostring(req.id) .. " (" .. #req.calls .. " calls)")
        ExecuteInGameThread(function()
            local ok, result = pcall(UEB.batch, req.calls)
            trace("idle after id=" .. tostring(req.id))
            if ok then respond(req.id, true, result, {}, nil, started)
            else respond(req.id, false, nil, {}, tostring(result), started) end
            busy = false
        end)
        return
    end
    if req.op ~= "eval" or type(req.code) ~= "string" then
        respond(req.id, false, nil, {}, "unknown op or missing code", started)
        return
    end
    if not SETTINGS.allow_eval then
        respond(req.id, false, nil, {},
            (EVAL_FORCED_OFF
                and "eval refused: allow_writes = false forces allow_eval off (eval can write); set "
                    .. "allow_writes = true in " .. MOD_NAME .. "/scripts/settings.lua (batch ops still work)"
                or "eval refused: allow_eval = false in " .. MOD_NAME .. "/scripts/settings.lua (batch ops still work)"),
            started)
        return
    end
    busy = true
    trace("eval id=" .. tostring(req.id) .. " " .. req.code:gsub("%s+", " "))
    ExecuteInGameThread(function()
        local ok, result, output, err = runEval(req.code)
        trace("idle after id=" .. tostring(req.id))
        respond(req.id, ok, result, output, err, started)
        busy = false
    end)
end

-- UEB.reload() re-runs this file in place; the generation bump retires the previous poll loop.
UEB_GENERATION = (UEB_GENERATION or 0) + 1
local myGeneration = UEB_GENERATION
function UEB.reload()
    dofile(MOD_PATH)
    return "reloaded, generation " .. tostring(UEB_GENERATION)
end

if not SETTINGS.enabled then
    log("disabled by scripts/settings.lua (enabled = false); not polling")
    return
end

LoopAsync(POLL_MS, function()
    if myGeneration ~= UEB_GENERATION then return true end
    if busy then return false end
    local raw = readFile(REQUEST)
    if not raw then return false end
    os.remove(REQUEST)
    local ok, req = pcall(json.decode, raw)
    if not ok or type(req) ~= "table" then
        respond("?", false, nil, {}, "bad request json: " .. tostring(req), os.clock())
        return false
    end
    local okH, err = pcall(handle, req)
    if not okH then
        busy = false
        respond(req.id, false, nil, {}, "handler: " .. tostring(err), os.clock())
    end
    return false
end)

log("v%s ready (protocol %d, generation %d), polling %s every %d ms; eval=%s writes=%s",
    VERSION, PROTOCOL, myGeneration, REQUEST, POLL_MS,
    tostring(SETTINGS.allow_eval), tostring(SETTINGS.allow_writes))
