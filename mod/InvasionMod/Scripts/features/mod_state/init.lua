-- Feature mod_state (M01): keeps the values of the Invasion Mod inside the save, through the shared module ModState.
-- Other features open the same state with ModState.open(MOD, "pawn") and register their own keys. They never write Tags.
local core = require("ManorCore")
local ModState = require("ModState")
local config = require("config").mod_state

local TAG = "InvasionMod.mod_state"
local MOD = "invasion"
local STATE_VERSION = 1
local PAWN_BEGIN_PLAY = "/Game/CPP_BP/MyPawnCPP_BP3.MyPawnCPP_BP3_C:ReceiveBeginPlay"
local LOAD_POLL_MS = 500
local LOAD_MAX_POLLS = 240
local HOOK_RETRY_MS = 3000
local HOOK_MAX_ATTEMPTS = 40
local TEST_TAG_PATTERN = "^mstest_[A-Za-z0-9_]+$"

local state = ModState.open(MOD, "pawn", STATE_VERSION)
for _, entry in ipairs(config.keys) do state:register(entry.key, entry.default, entry.kind) end

---------------------------------------------------------------------------------------------
-- Load after each game load
---------------------------------------------------------------------------------------------

local function reload_state(reason)
    core.log.try(TAG, function()
        state:load()
        core.log.info(TAG, string.format("state loaded (%s): stored version %s, %d unknown entries", reason, tostring(state.stored_version), #state.unknown))
    end)
end

-- The pawn exists already when the mod is reloaded in a running game. At game start the pawn does not exist yet.
if state:owner_object() ~= nil then reload_state("mod start") end

-- At ReceiveBeginPlay the engine does not hold the new pawn yet (seen in the real game). So the load waits until it does.
local function load_when_pawn_is_ready()
    local tries = 0
    local finished = false
    LoopAsync(LOAD_POLL_MS, function()
        if finished then return true end
        tries = tries + 1
        ExecuteInGameThread(function()
            if finished then return end
            if state:owner_object() ~= nil then
                finished = true
                reload_state("pawn ready after " .. tries .. " polls")
            elseif tries >= LOAD_MAX_POLLS then
                finished = true
                core.log.error(TAG, "the player pawn did not become available: ModState values are not loaded")
            end
        end)
        return false
    end)
end

local function hook_begin_play()
    RegisterHook(PAWN_BEGIN_PLAY, load_when_pawn_is_ready)
end

-- The pawn class is a Blueprint class. It loads after the mod, so the hook is tried again until it works.
local attempts = 0
LoopAsync(HOOK_RETRY_MS, function()
    attempts = attempts + 1
    if pcall(hook_begin_play) then
        core.log.info(TAG, "hooked " .. PAWN_BEGIN_PLAY)
        return true
    end
    if attempts >= HOOK_MAX_ATTEMPTS then
        core.log.error(TAG, "gave up hooking " .. PAWN_BEGIN_PLAY .. ": values would not load after a game load")
        return true
    end
    return false
end)

---------------------------------------------------------------------------------------------
-- Named commands for the harness (no eval)
---------------------------------------------------------------------------------------------

local has_commands, commands = pcall(require, "HarnessCommands")

local function key_argument() return { type = "string", required = true, maxLength = 40 } end

-- Only the keys of this feature (config.keys). Other features share the state and register their own keys.
local function command_dump()
    local dump = state:dump()
    local own_values, own_kinds = {}, {}
    for _, entry in ipairs(config.keys) do
        own_values[entry.key] = dump.values[entry.key]
        own_kinds[entry.key] = dump.kinds[entry.key]
    end
    dump.values, dump.kinds = own_values, own_kinds
    return dump
end

local function command_get(args)
    local ok, value = pcall(state.get, state, args.key)
    if not ok then return nil, tostring(value) end
    return { key = args.key, value = value }
end

local function command_set(args)
    local kind = state.kinds[args.key]
    if kind == nil then return nil, "key '" .. args.key .. "' is not registered for mod '" .. MOD .. "'" end
    local value, reason = ModState.decode(kind, args.value)
    if reason then return nil, reason end
    local ok, error_text = pcall(state.set, state, args.key, value)
    if not ok then return nil, tostring(error_text) end
    return { key = args.key, value = state:get(args.key) }
end

-- Adds a Tag that is not ours. A scenario uses it to prove that a flush leaves other Tags alone (A6).
local function command_add_foreign_tag(args)
    if not args.tag:match(TEST_TAG_PATTERN) then return nil, "tag must match " .. TEST_TAG_PATTERN end
    local object = state:owner_object()
    if object == nil then return nil, "no live player pawn" end
    local tags = object.Tags
    tags[#tags + 1] = FName(args.tag)
    return { count = #tags }
end


-- Tags limits (#283): write or read many test entries on a pawn, an AI lord or a building. Names start with "tlimit:".
local function tags_limit_target(args)
    if args.target == "pawn" then return state:owner_object() end
    local class = args.target == "lord" and "PawnCPP_AI" or "SMBuildingMaster"
    local list = FindAllOf(class) or {}
    local object = list[(args.index or 1)]
    if object ~= nil and object:IsValid() then return object end
    return nil
end

local function command_tags_limit_write(args)
    local object = tags_limit_target(args)
    if object == nil then return nil, "no target " .. args.target end
    local started = os.clock()
    local tags = object.Tags
    local padding = string.rep("x", math.max(0, args.size - 12))
    local first = #tags + 1
    for i = 1, args.count do
        tags[#tags + 1] = FName(string.format("tlimit:%s%05d=%s", args.label, i, padding))
    end
    return { target = object:GetFullName(), total_tags = #object.Tags, added = #object.Tags - first + 1, seconds = os.clock() - started }
end

local function command_tags_limit_read(args)
    local object = tags_limit_target(args)
    if object == nil then return nil, "no target " .. args.target end
    local started = os.clock()
    local tags = object.Tags
    local count, chars, longest, sample = 0, 0, 0, nil
    for i = 1, #tags do
        local text = tags[i]:ToString()
        if text:sub(1, 7 + #args.label) == "tlimit:" .. args.label then
            count = count + 1
            chars = chars + #text
            if #text > longest then longest = #text end
            sample = sample or text:sub(1, 40)
        end
    end
    local last = #tags > 0 and tags[#tags]:ToString() or ""
    return { last_len = #last, last_head = last:sub(1, 30), target = object:GetFullName(), total_tags = #tags, entry_count = count, entry_chars = chars, longest = longest, sample = sample, seconds = os.clock() - started }
end

if has_commands then
    commands.register("InvasionMod.mod_state_dump", command_dump, {})
    commands.register("InvasionMod.mod_state_get", command_get, { key = key_argument() })
    commands.register("InvasionMod.mod_state_set", command_set, { key = key_argument(), value = { type = "string", required = true, maxLength = 60 } })
    commands.register("InvasionMod.mod_state_add_foreign_tag", command_add_foreign_tag, { tag = { type = "string", required = true, maxLength = 40 } })
    local tags_limit_args = { target = { type = "string", required = true, maxLength = 8 }, label = { type = "string", required = true, maxLength = 20 }, index = { type = "number", min = 1, max = 500 } }
    local write_args = { count = { type = "number", required = true, min = 1, max = 5000 }, size = { type = "number", required = true, min = 12, max = 20000 } }
    for k, v in pairs(tags_limit_args) do write_args[k] = v end
    commands.register("InvasionMod.tags_limit_write", command_tags_limit_write, write_args)
    commands.register("InvasionMod.tags_limit_read", command_tags_limit_read, tags_limit_args)
end

core.log.info(TAG, "feature mod_state loaded")
return { state = state }
