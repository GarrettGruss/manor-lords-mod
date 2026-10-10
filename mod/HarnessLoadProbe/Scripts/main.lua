-- HarnessLoadProbe: manual test for loading a save from the main menu (spec 02, plan step 2).
-- Press F8 in the main menu. The mod opens the load screen, finds the target slot in the slot
-- list, and calls mainMenu_widget_C:LoadGame with that list entry.
-- Every step is logged with HarnessLog (ue4ss/harness/mod.log) so a failure shows which step broke.
-- This mod is only a probe. The final logic goes to HarnessBoot.

local log = require("HarnessLog")

local VERSION = "1"
local TAG = "LoadProbe"
local POLL_MS = 500
local POLL_LIMIT = 40 -- 40 polls of 500 ms = 20 s

local function targetSlot()
    local fromEnv = os.getenv and os.getenv("HARNESS_TEST_SAVE")
    if fromEnv and fromEnv ~= "" then return fromEnv end
    return "saveGame_0"
end

-- Turn an FString, FName or Lua string into a Lua string. Returns nil if that is not possible.
local function asText(value)
    if type(value) == "string" then return value end
    if value == nil then return nil end
    local ok, text = pcall(function() return value:ToString() end)
    if ok then return text end
    return nil
end

-- A TArray element can be a wrapper that needs :get(). Unwrap it only if it has :get().
local function unwrap(element)
    local ok, inner = pcall(function() return element:get() end)
    if ok and inner ~= nil then return inner end
    return element
end

-- Find the list entry (a SaveGameSlot struct) whose descriptor has the wanted file slot name.
local function findSlotEntry(screen, wanted)
    local slots = screen.SortedSlotsByDate
    local count = slots:GetArrayNum()
    log.info(TAG, "slot list has " .. count .. " entries; looking for saveSlot '" .. wanted .. "'")
    for i = 1, count do
        local entry = unwrap(slots[i])
        local okDescr, descr = pcall(function() return entry.Descriptor end)
        if okDescr and descr ~= nil and descr:IsValid() then
            local name = asText(descr.saveSlot)
            if name == wanted then
                log.info(TAG, "found '" .. wanted .. "' at list position " .. i .. ", SlotIndex "
                    .. tostring(entry.SlotIndex) .. ", level " .. tostring(asText(descr.LevelName)))
                return entry
            end
        end
    end
    return nil
end

local function loadSlot(wanted)
    local widget = FindFirstOf("mainMenu_widget_C")
    if widget == nil or not widget:IsValid() then
        log.error(TAG, "mainMenu_widget_C not found. Is the game at the main menu?")
        return
    end

    log.info(TAG, "step 1: SwitchToLoadScreen(false)")
    local okSwitch, errSwitch = pcall(function() widget:SwitchToLoadScreen(false) end)
    if not okSwitch then
        log.error(TAG, "SwitchToLoadScreen failed: " .. tostring(errSwitch))
        return
    end

    local polls = 0
    local finished = false
    LoopAsync(POLL_MS, function()
        if finished then return true end
        -- Game objects are touched only on the game thread.
        ExecuteInGameThread(function()
            if finished then return end
            polls = polls + 1
            local screen = FindFirstOf("W_MainMenu_SaveLoadScreenV2_C")
            local ready = false
            if screen ~= nil and screen:IsValid() then
                local okCount, count = pcall(function() return screen.SortedSlotsByDate:GetArrayNum() end)
                ready = okCount and count > 0
            end
            if not ready then
                if polls >= POLL_LIMIT then
                    finished = true
                    log.error(TAG, "step 2: slot list still empty after " .. polls .. " polls; giving up")
                end
                return
            end

            finished = true
            log.info(TAG, "step 2: slot list ready after " .. polls .. " polls")
            local entry = findSlotEntry(screen, wanted)
            if entry == nil then
                log.error(TAG, "step 3: slot '" .. wanted .. "' is not in the list")
                return
            end
            log.info(TAG, "step 4: calling mainMenu_widget_C:LoadGame")
            local okLoad, errLoad = pcall(function() widget:LoadGame(entry) end)
            if okLoad then
                log.info(TAG, "step 4: LoadGame returned without error")
            else
                log.error(TAG, "step 4: LoadGame failed: " .. tostring(errLoad))
            end
        end)
        return false
    end)
end

RegisterKeyBind(Key.F8, function()
    local wanted = targetSlot()
    log.say(TAG, "F8 pressed; target slot '" .. wanted .. "'")
    ExecuteInGameThread(function()
        log.try(TAG, loadSlot, wanted)
    end)
end)

log.info("HarnessLoadProbe", "loaded version " .. VERSION)
log.say(TAG, "ready. Press F8 in the main menu to load slot '" .. targetSlot() .. "'.")
