-- HarnessBoot: loads the test save from the main menu and reports when the game is ready.
-- Spec: docs/specs/02-save-autoload/README.md
--
-- The mod does nothing unless the harness turns it on. This keeps normal play safe.
--   Turn on: set env HARNESS_AUTOBOOT=1, or create the file <harness dir>/autoboot.enable.
--   Save to load: env HARNESS_TEST_SAVE (file slot name, for example "saveGame_0").
--   Output folder: env HARNESS_RUN_DIR, or ue4ss/harness (same as HarnessLog).
--
-- Output files:
--   boot.json     current state and the history of state changes. Always up to date.
--   ready.marker  written once, when the game is ready for a scenario.
--
-- States: WAITING_FOR_MENU -> LOADING_SAVE -> WAITING_FOR_READY -> PAUSING -> READY.
-- Any wait can go to FAILED. READY means the game clock was measured as stopped.
-- Rule: game objects are touched only on the game thread (ExecuteInGameThread).

local log = require("HarnessLog")

local TAG = "HarnessBoot"
local DEFAULT_SLOT = "saveGame_0"

local POLL_MS = 500
local TIMEOUT_S = {
    WAITING_FOR_MENU = 120,
    LOADING_SAVE = 30,
    WAITING_FOR_READY = 180,
    PAUSING = 60,
}
-- The ready check must pass this many polls in a row. This avoids a short false "ready".
local READY_STABLE_POLLS = 3
-- The game clock counts as stopped when it moves less than this between two polls (in game seconds).
local CLOCK_STOPPED_EPSILON = 0.001
-- The clock must stay stopped for this many polls in a row.
local CLOCK_STOPPED_POLLS = 3
-- Wait at least this long between two pauseGame calls (seconds).
local PAUSE_RETRY_S = 2

local OUT_DIR = log.dir()
local BOOT_FILE = OUT_DIR .. "/boot.json"
local READY_FILE = OUT_DIR .. "/ready.marker"
local ENABLE_FILE = "ue4ss/harness/autoboot.enable"

---------------------------------------------------------------------------------------------
-- Settings
---------------------------------------------------------------------------------------------

local function fileExists(path)
    local f = io.open(path, "rb")
    if f then f:close() return true end
    return false
end

local function isEnabled()
    local flag = os.getenv and os.getenv("HARNESS_AUTOBOOT")
    if flag == "1" then return true end
    return fileExists(ENABLE_FILE)
end

local function targetSlot()
    local fromEnv = os.getenv and os.getenv("HARNESS_TEST_SAVE")
    if fromEnv and fromEnv ~= "" then return fromEnv end
    return DEFAULT_SLOT
end

---------------------------------------------------------------------------------------------
-- Small helpers
---------------------------------------------------------------------------------------------

local function jsonString(text)
    text = tostring(text):gsub("\\", "\\\\"):gsub('"', '\\"'):gsub("\n", "\\n"):gsub("\r", "")
    return '"' .. text .. '"'
end

-- Write a file so a reader never sees half of it: write a .tmp file, then rename it.
local function writeAtomic(path, text)
    local tmp = path .. ".tmp"
    local f, err = io.open(tmp, "wb")
    if not f then
        log.error(TAG, "cannot write " .. tmp .. ": " .. tostring(err))
        return false
    end
    f:write(text)
    f:close()
    os.remove(path) -- os.rename does not replace an existing file on Windows
    local ok, renameErr = os.rename(tmp, path)
    if not ok then
        log.error(TAG, "cannot rename " .. tmp .. ": " .. tostring(renameErr))
        return false
    end
    return true
end

-- Turn an FString, FName or Lua string into a Lua string. Returns nil if that is not possible.
local function asText(value)
    if type(value) == "string" then return value end
    if value == nil then return nil end
    local ok, text = pcall(function() return value:ToString() end)
    if ok then return text end
    return nil
end

-- A TArray element can be a wrapper that needs :get(). Unwrap it only if that works.
local function unwrap(element)
    local ok, inner = pcall(function() return element:get() end)
    if ok and inner ~= nil then return inner end
    return element
end

local function isValid(object)
    if object == nil then return false end
    local ok, valid = pcall(function() return object:IsValid() end)
    return ok and valid == true
end

---------------------------------------------------------------------------------------------
-- State and boot.json
---------------------------------------------------------------------------------------------

local boot = {
    state = "WAITING_FOR_MENU",
    slot = targetSlot(),
    started = os.time(),
    reason = nil,
    history = {},
}
local stateSince = os.time()

local function writeBootFile()
    local rows = {}
    for _, change in ipairs(boot.history) do
        rows[#rows + 1] = string.format('{"state":%s,"time":%d}', jsonString(change.state), change.time)
    end
    local text = string.format(
        '{"state":%s,"slot":%s,"started":%d,"updated":%d,"reason":%s,"history":[%s]}\n',
        jsonString(boot.state), jsonString(boot.slot), boot.started, os.time(),
        boot.reason and jsonString(boot.reason) or "null", table.concat(rows, ","))
    writeAtomic(BOOT_FILE, text)
end

local function setState(name, reason)
    boot.state = name
    boot.reason = reason
    stateSince = os.time()
    boot.history[#boot.history + 1] = { state = name, time = os.time() }
    log.info(TAG, "state -> " .. name .. (reason and (": " .. reason) or ""))
    writeBootFile()
end

local function fail(reason)
    log.error(TAG, "FAILED: " .. reason)
    setState("FAILED", reason)
end

local function secondsInState()
    return os.time() - stateSince
end

---------------------------------------------------------------------------------------------
-- Step: WAITING_FOR_MENU
---------------------------------------------------------------------------------------------

local function stepWaitingForMenu()
    local widget = FindFirstOf("mainMenu_widget_C")
    if isValid(widget) then
        setState("LOADING_SAVE")
        boot.loadPhase = "check_save"
        return
    end
    if secondsInState() > TIMEOUT_S.WAITING_FOR_MENU then
        fail("main menu widget did not appear in " .. TIMEOUT_S.WAITING_FOR_MENU .. " s")
    end
end

---------------------------------------------------------------------------------------------
-- Step: LOADING_SAVE
-- Phases: check_save -> wait_slots -> done. The phase is kept in boot.loadPhase.
---------------------------------------------------------------------------------------------

-- Find the list entry (a SaveGameSlot struct) whose descriptor has the wanted file slot name.
local function findSlotEntry(screen, wanted)
    local slots = screen.SortedSlotsByDate
    local count = slots:GetArrayNum()
    for i = 1, count do
        local entry = unwrap(slots[i])
        local okDescr, descr = pcall(function() return entry.Descriptor end)
        if okDescr and isValid(descr) and asText(descr.saveSlot) == wanted then
            log.info(TAG, string.format("found '%s' in a list of %d (position %d, SlotIndex %s, level %s)",
                wanted, count, i, tostring(entry.SlotIndex), tostring(asText(descr.LevelName))))
            return entry
        end
    end
    return nil, count
end

local function checkSaveExists()
    -- A missing save is a clear failure. If the check itself cannot run, go on without it.
    local okFind, handler = pcall(StaticFindObject, "/Script/ManorLords.Default__IoHandler")
    if not okFind or not isValid(handler) then
        log.warn(TAG, "IoHandler not found; skipping the save exists check")
        return true
    end
    local okCall, exists = pcall(function() return handler:DoesSaveGameExist(boot.slot) end)
    if not okCall then
        log.warn(TAG, "DoesSaveGameExist failed (" .. tostring(exists) .. "); skipping the check")
        return true
    end
    return exists == true
end

local function stepLoadingSave()
    local widget = FindFirstOf("mainMenu_widget_C")
    if not isValid(widget) then
        fail("main menu widget disappeared while loading the save")
        return
    end

    if boot.loadPhase == "check_save" then
        if not checkSaveExists() then
            fail("save slot '" .. boot.slot .. "' does not exist")
            return
        end
        log.info(TAG, "opening the load screen")
        local ok, err = pcall(function() widget:SwitchToLoadScreen(false) end)
        if not ok then
            fail("SwitchToLoadScreen failed: " .. tostring(err))
            return
        end
        boot.loadPhase = "wait_slots"
        return
    end

    if boot.loadPhase == "wait_slots" then
        local screen = FindFirstOf("W_MainMenu_SaveLoadScreenV2_C")
        local count = 0
        if isValid(screen) then
            local okCount, n = pcall(function() return screen.SortedSlotsByDate:GetArrayNum() end)
            if okCount then count = n end
        end
        -- The game fills the slot list while it scans the save folder. A list that is not empty
        -- may still be incomplete (10 of 29 entries was seen). Keep polling until the wanted slot
        -- shows up, and fail only when the time limit ends.
        local entry = nil
        if count > 0 then entry = findSlotEntry(screen, boot.slot) end
        if entry ~= nil then
            log.info(TAG, "calling LoadGame")
            local okLoad, errLoad = pcall(function() widget:LoadGame(entry) end)
            if not okLoad then
                fail("LoadGame failed: " .. tostring(errLoad))
                return
            end
            boot.loadPhase = "done"
            setState("WAITING_FOR_READY")
            return
        end
    end

    if secondsInState() > TIMEOUT_S.LOADING_SAVE then
        fail("slot '" .. boot.slot .. "' did not appear in the save list in " .. TIMEOUT_S.LOADING_SAVE .. " s")
    end
end

---------------------------------------------------------------------------------------------
-- Step: WAITING_FOR_READY
---------------------------------------------------------------------------------------------

-- Returns the engine actor, the player pawn, and a table of check results (for the log).
local function checkReady()
    local checks = { engine = false, player = false, regions = false, settled = false }
    local engine = FindFirstOf("RTSMultiEngineCPP")
    if not isValid(engine) then return nil, nil, checks end
    checks.engine = true

    local okPlayer, player = pcall(function() return engine.playerRef end)
    checks.player = okPlayer and isValid(player)

    local okRegions, regions = pcall(function() return engine.regions end)
    if okRegions and regions ~= nil then
        local okCount, count = pcall(function() return regions:GetArrayNum() end)
        checks.regions = okCount and count > 0
        if checks.regions then
            for i = 1, count do
                local region = unwrap(regions[i])
                local okSettled, settled = pcall(function() return region.isSettled end)
                if okSettled and settled == true then
                    checks.settled = true
                    break
                end
            end
        end
    end
    return engine, player, checks
end

local function allTrue(checks)
    return checks.engine and checks.player and checks.regions and checks.settled
end

local function describeChecks(checks)
    return string.format("engine=%s player=%s regions=%s settled=%s",
        tostring(checks.engine), tostring(checks.player), tostring(checks.regions), tostring(checks.settled))
end

local function readCalendar(engine)
    local calendar = {}
    local okTc, tc = pcall(function() return engine.TemporalComponent end)
    if okTc and isValid(tc) then
        for _, name in ipairs({ "day", "month", "Year", "Season" }) do
            local ok, value = pcall(function() return tc[name] end)
            calendar[name] = ok and value or nil
        end
    end
    return calendar
end

local function writeReadyMarker(engine, clock)
    local cal = readCalendar(engine)
    -- "paused" is true only because the game clock was measured as stopped (see stepPausing).
    local text = string.format(
        '{"slot":%s,"time":%d,"seconds_since_start":%d,"paused":true,"clock":%s,"day":%s,"month":%s,"year":%s,"season":%s}\n',
        jsonString(boot.slot), os.time(), os.time() - boot.started, tostring(clock),
        tostring(cal.day), tostring(cal.month), tostring(cal.Year), tostring(cal.Season))
    return writeAtomic(READY_FILE, text)
end

local stablePolls = 0

local function stepWaitingForReady()
    local _, _, checks = checkReady()
    if allTrue(checks) then
        stablePolls = stablePolls + 1
        if stablePolls >= READY_STABLE_POLLS then
            setState("PAUSING")
            return
        end
    else
        stablePolls = 0
    end
    if secondsInState() > TIMEOUT_S.WAITING_FOR_READY then
        fail("game was not ready in " .. TIMEOUT_S.WAITING_FOR_READY .. " s (" .. describeChecks(checks) .. ")")
    end
end

---------------------------------------------------------------------------------------------
-- Step: PAUSING
-- The flag PawnCPP.bIsPlayerPaused is not reliable: it read true while game time was running.
-- So this step calls pauseGame and then reads the game clock. The game is paused only when the
-- clock stays still for several polls. If the clock still moves, pauseGame is called again.
---------------------------------------------------------------------------------------------

local pausing = { lastClock = nil, sawRunning = false, stoppedPolls = 0, lastCallAt = 0, calls = 0 }

local function callPauseGame(engine)
    local okPlayer, player = pcall(function() return engine.playerRef end)
    if not okPlayer or not isValid(player) then
        log.warn(TAG, "player pawn not available for pauseGame")
        return
    end
    pausing.calls = pausing.calls + 1
    pausing.lastCallAt = os.time()
    log.info(TAG, "game clock is moving; calling pauseGame (call " .. pausing.calls .. ")")
    local ok, err = pcall(function() player:pauseGame() end)
    if not ok then log.warn(TAG, "pauseGame failed: " .. tostring(err)) end
end

local function stepPausing()
    local engine = FindFirstOf("RTSMultiEngineCPP")
    if not isValid(engine) then
        fail("engine actor disappeared while pausing")
        return
    end

    local okClock, clock = pcall(function() return engine:getGameTimeAdjusted() end)
    if not okClock or type(clock) ~= "number" then
        fail("cannot read the game clock: " .. tostring(clock))
        return
    end

    local hasPrevious = pausing.lastClock ~= nil
    local moved = hasPrevious and math.abs(clock - pausing.lastClock) >= CLOCK_STOPPED_EPSILON
    pausing.lastClock = clock

    -- Right after a load the clock stands at 0 for a few seconds, because the game itself holds the
    -- speed at 0. That is not a pause: the game then sets the speed to 1x and would undo ours.
    -- So wait until the clock has moved at least once, and only then pause and check again.
    if moved then
        pausing.sawRunning = true
        pausing.stoppedPolls = 0
        if os.time() - pausing.lastCallAt >= PAUSE_RETRY_S then callPauseGame(engine) end
    elseif hasPrevious and pausing.sawRunning then
        pausing.stoppedPolls = pausing.stoppedPolls + 1
        if pausing.stoppedPolls >= CLOCK_STOPPED_POLLS then
            if writeReadyMarker(engine, clock) then
                setState("READY")
            else
                fail("could not write ready.marker")
            end
            return
        end
    end

    if secondsInState() > TIMEOUT_S.PAUSING then
        local why = pausing.sawRunning and "the clock did not stop" or "the clock never started"
        fail("game clock did not stop in " .. TIMEOUT_S.PAUSING .. " s (" .. why .. ", "
            .. pausing.calls .. " pauseGame calls)")
    end
end

---------------------------------------------------------------------------------------------
-- Main loop
---------------------------------------------------------------------------------------------

local STEPS = {
    WAITING_FOR_MENU = stepWaitingForMenu,
    LOADING_SAVE = stepLoadingSave,
    WAITING_FOR_READY = stepWaitingForReady,
    PAUSING = stepPausing,
}

local function finished()
    return boot.state == "READY" or boot.state == "FAILED"
end

local function runStep()
    local step = STEPS[boot.state]
    if step == nil then return end
    local ok, err = pcall(step)
    if not ok then fail("error in " .. boot.state .. ": " .. tostring(err)) end
end

if not isEnabled() then
    log.info(TAG, "off (set HARNESS_AUTOBOOT=1 or create " .. ENABLE_FILE .. " to turn it on)")
    return
end

-- A stale ready marker from an earlier run must never be read as a new "ready".
os.remove(READY_FILE)
log.say(TAG, "on; will load slot '" .. boot.slot .. "'; output in " .. OUT_DIR)
setState("WAITING_FOR_MENU")

LoopAsync(POLL_MS, function()
    if finished() then return true end
    ExecuteInGameThread(function()
        if not finished() then runStep() end
    end)
    return false
end)
