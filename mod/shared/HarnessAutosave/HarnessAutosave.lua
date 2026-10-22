-- HarnessAutosave: read the autosave timer of the game, and push the timer far into the future.
-- Why: the game's own autosave writes into the user's REAL save folder, also when a run has a private LOCALAPPDATA.
-- Spec: openspec/changes/archive/2026-10-15-legacy-06-dev-loop-and-fixtures/implementation-notes/autosave.md
--
-- How the game does it (jmap): the player pawn (MyPawnCPP_BP3_C) owns a timer, `autosaveHandle`.
-- The timer calls the pawn event 'Request Autosave'. The game instance (MLGameInstance) has
--   Settings.autosavePeriod            the stored period in seconds (default 600; it is saved in rtsSettings.sav)
--   SetAutosavePeriodOnPawn(seconds)   restarts the pawn timer with a new period. It does not change Settings.
-- This module never calls a function that saves (see CLAUDE.md, Safety). It does not call SetAutosavePeriod,
-- because that native function may also write the settings file into the user's save folder.

local M = {}

-- One year in seconds. A float timer rate can hold it exactly.
M.DISABLED_PERIOD_S = 31536000

local TIMER_LIBRARY = "/Script/Engine.Default__KismetSystemLibrary"

local function isValid(object)
    if object == nil then return false end
    local ok, valid = pcall(function() return object:IsValid() end)
    return ok and valid == true
end

-- Run `read` and put its value, or its error text, into `out[name]`.
local function attempt(out, name, read)
    local ok, value = pcall(read)
    if not ok then
        out[name .. "_error"] = tostring(value)
        return nil
    end
    local kind = type(value)
    -- The result is written as JSON, so a game object or struct is kept out of it.
    if kind == "number" or kind == "string" or kind == "boolean" then out[name] = value end
    return value
end

local function findObjects()
    local engine = FindFirstOf("RTSMultiEngineCPP")
    local pawn = nil
    if isValid(engine) then
        local ok, player = pcall(function() return engine.playerRef end)
        if ok and isValid(player) then pawn = player end
    end
    local instance = FindFirstOf("MLGameInstance")
    return pawn, isValid(instance) and instance or nil
end

-- Read the values that show the state of the autosave timer. A value that cannot be read is
-- reported as `<name>_error`, so a caller sees what failed.
function M.status()
    local pawn, instance = findObjects()
    local out = {}
    if instance then
        attempt(out, "settings_period_s", function() return instance.Settings.autosavePeriod end)
    else
        out.instance_error = "no MLGameInstance"
    end
    if not pawn then
        out.pawn_error = "no player pawn"
        return out
    end
    local handle = attempt(out, "handle", function() return pawn.autosaveHandle end)
    if handle == nil then return out end
    attempt(out, "handle_id", function() return handle.Handle end)
    local library = StaticFindObject(TIMER_LIBRARY)
    if not isValid(library) then
        out.library_error = "no KismetSystemLibrary"
        return out
    end
    attempt(out, "timer_exists", function() return library:K2_TimerExistsHandle(pawn, handle) end)
    attempt(out, "remaining_s", function() return library:K2_GetTimerRemainingTimeHandle(pawn, handle) end)
    return out
end

-- A timer that is pushed this far (seconds) counts as disabled. The default period is 600 s.
M.MIN_DISABLED_REMAINING_S = 1000000

-- True if `status` (from M.status) shows a live timer that is far in the future.
function M.is_disabled(status)
    return status ~= nil and status.timer_exists == true
        and type(status.remaining_s) == "number" and status.remaining_s >= M.MIN_DISABLED_REMAINING_S
end

-- Restart the pawn timer with a very long period. Return the status before and after.
function M.disable(period_s)
    local pawn, instance = findObjects()
    if not instance then return nil, "no MLGameInstance" end
    if not pawn then return nil, "no player pawn" end
    period_s = period_s or M.DISABLED_PERIOD_S
    local before = M.status()
    local ok, answer = pcall(function() return instance:SetAutosavePeriodOnPawn(period_s) end)
    if not ok then return nil, "SetAutosavePeriodOnPawn failed: " .. tostring(answer) end
    return { before = before, after = M.status(), call_result = answer, period_s = period_s }
end

-- The game starts a new player pawn, with a new 600 s timer, after every world load.
M.PAWN_BEGIN_PLAY = "/Game/CPP_BP/MyPawnCPP_BP3.MyPawnCPP_BP3_C:ReceiveBeginPlay"
M.RETRY_DELAY_MS = 2000
M.RETRY_COUNT = 5

-- After READY, push the timer away again on each world load (the boot step only covers the first world).
-- `log` is HarnessLog (info and error). A failure is logged and does not stop the game.
-- Returns true if the hook was registered.
function M.guard_loads(log, tag, hook_path)
    local busy = false
    local function finish() busy = false end
    local function attemptPush(number)
        ExecuteWithDelay(M.RETRY_DELAY_MS, function()
            ExecuteInGameThread(function()
                local ok, changes, problem = pcall(M.disable)
                if ok and changes and M.is_disabled(changes.after) then
                    log.info(tag, string.format("autosave pushed away after a load: timer remaining %s s -> %s s (try %d)",
                        tostring(changes.before.remaining_s), tostring(changes.after.remaining_s), number))
                    finish()
                elseif number < M.RETRY_COUNT then
                    attemptPush(number + 1)
                else
                    log.error(tag, "autosave timer was not pushed away after a load (" .. M.RETRY_COUNT .. " tries): "
                        .. tostring(ok and (problem or (changes and changes.after and changes.after.remaining_s)) or changes))
                    finish()
                end
            end)
        end)
    end
    local registered, err = pcall(RegisterHook, hook_path or M.PAWN_BEGIN_PLAY, function()
        if busy then return end
        busy = true
        attemptPush(1)
    end)
    if not registered then log.error(tag, "cannot watch world loads for the autosave timer: " .. tostring(err)) end
    return registered
end

return M
