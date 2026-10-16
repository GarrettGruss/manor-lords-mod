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

local function command_dump()
    return state:dump()
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

if has_commands then
    commands.register("InvasionMod.mod_state_dump", command_dump, {})
    commands.register("InvasionMod.mod_state_get", command_get, { key = key_argument() })
    commands.register("InvasionMod.mod_state_set", command_set, { key = key_argument(), value = { type = "string", required = true, maxLength = 60 } })
    commands.register("InvasionMod.mod_state_add_foreign_tag", command_add_foreign_tag, { tag = { type = "string", required = true, maxLength = 40 } })
end

core.log.info(TAG, "feature mod_state loaded")
return { state = state }
