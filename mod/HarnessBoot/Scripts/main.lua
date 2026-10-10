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
-- States: WAITING_FOR_MENU -> LOADING_SAVE -> WAITING_FOR_READY -> READY. Any wait can go to FAILED.
-- Rule: game objects are touched only on the game thread (ExecuteInGameThread).

local log = require("HarnessLog")

local TAG = "HarnessBoot"
local DEFAULT_SLOT = "saveGame_0"

local POLL_MS = 500
local TIMEOUT_S = {
    WAITING_FOR_MENU = 120,
    LOADING_SAVE = 30,
    WAITING_FOR_READY = 180,
}
-- The ready check must pass this many polls in a row. This avoids a short false "ready".
local READY_STABLE_POLLS = 3

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
        if count > 0 then
            local entry, listed = findSlotEntry(screen, boot.slot)
            if entry == nil then
                fail("slot '" .. boot.slot .. "' is not in the save list (" .. tostring(listed) .. " entries)")
                return
            end
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
        fail("save list was not ready in " .. TIMEOUT_S.LOADING_SAVE .. " s")
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

local function writeReadyMarker(engine, player)
    local paused = nil
    local okPaused, value = pcall(function() return player.bIsPlayerPaused end)
    if okPaused then paused = value end

    local cal = readCalendar(engine)
    local text = string.format(
        '{"slot":%s,"time":%d,"seconds_since_start":%d,"paused":%s,"day":%s,"month":%s,"year":%s,"season":%s}\n',
        jsonString(boot.slot), os.time(), os.time() - boot.started, tostring(paused),
        tostring(cal.day), tostring(cal.month), tostring(cal.Year), tostring(cal.Season))
    return writeAtomic(READY_FILE, text)
end

-- The game is already paused after a load. Pause it only if it is not, so the harness
-- decides when time starts. The pawn function pauseGame is the one from the jmap findings.
local function ensurePaused(player)
    local okPaused, paused = pcall(function() return player.bIsPlayerPaused end)
    if okPaused and paused == true then return end
    log.info(TAG, "game is not paused; calling pauseGame")
    local ok, err = pcall(function() player:pauseGame() end)
    if not ok then log.warn(TAG, "pauseGame failed: " .. tostring(err)) end
end

local stablePolls = 0

local function stepWaitingForReady()
    local engine, player, checks = checkReady()
    if allTrue(checks) then
        stablePolls = stablePolls + 1
        if stablePolls >= READY_STABLE_POLLS then
            ensurePaused(player)
            if writeReadyMarker(engine, player) then
                setState("READY")
            else
                fail("could not write ready.marker")
            end
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
-- Main loop
---------------------------------------------------------------------------------------------

local STEPS = {
    WAITING_FOR_MENU = stepWaitingForMenu,
    LOADING_SAVE = stepLoadingSave,
    WAITING_FOR_READY = stepWaitingForReady,
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
