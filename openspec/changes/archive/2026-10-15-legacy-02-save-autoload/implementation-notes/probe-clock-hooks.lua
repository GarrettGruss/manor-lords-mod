-- HarnessProbeClock: TEMPORARY probe. It logs who pauses, unpauses and changes the speed of the game clock.
-- Spec: openspec/changes/archive/2026-10-15-legacy-02-save-autoload/implementation-notes/clock-restart-cause.md
-- Every hook is cheap and guarded. The mod only reads. It calls no function that saves.

local log = require("HarnessLog")
local TAG = "Probe"

local HOOKS = {
    "/Script/ManorLords.PawnCPP:pauseGame",
    "/Script/ManorLords.PawnCPP:unPauseGame",
    "/Script/ManorLords.PawnCPP:setGameSpeed",
    "/Script/ManorLords.PawnCPP:toggleTimePause",
    "/Script/ManorLords.PawnCPP:togglePauseMenu",
    "/Script/ManorLords.PawnCPP:updateGameSpeedUI",
    "/Script/ManorLords.RTSMultiEngineCPP:setGameSpeed",
    "/Script/ManorLords.RTSMultiEngineCPP:resetCoreTimers",
    "/Script/Engine.GameplayStatics:SetGamePaused",
    "/Script/Engine.GameplayStatics:SetGlobalTimeDilation",
    "/Script/Engine.PlayerController:Pause",
    "/Game/CPP_BP/MyPawnCPP_BP3.MyPawnCPP_BP3_C:changeGameSpeed",
    "/Game/CPP_BP/MyPawnCPP_BP3.MyPawnCPP_BP3_C:increaseGameSpeed",
    "/Game/CPP_BP/MyPawnCPP_BP3.MyPawnCPP_BP3_C:decreaseGameSpeed",
    "/Game/CPP_BP/MyPawnCPP_BP3.MyPawnCPP_BP3_C:setGamePausedInclVamp",
    "/Game/CPP_BP/MyPawnCPP_BP3.MyPawnCPP_BP3_C:toggleTimePause",
    "/Game/CPP_BP/MyPawnCPP_BP3.MyPawnCPP_BP3_C:storeOrBringBackGameSpeedAndZoomAfterMapMenuToggle",
    "/Game/CPP_BP/MyPawnCPP_BP3.MyPawnCPP_BP3_C:ClosePauseMenu",
    "/Game/CPP_BP/MyPawnCPP_BP3.MyPawnCPP_BP3_C:OpenPauseMenu",
    "/Game/UI/Main_Menu/mainMenu_widget.mainMenu_widget_C:unpauseAndResetDLSS",
    "/Game/UI/Main_Menu/mainMenu_widget.mainMenu_widget_C:closeLevel",
    "/Game/UI/Main_Menu/mainMenu_widget.mainMenu_widget_C:OnSaveLoadMenuClosed_Event",
    "/Game/UI/Main_Menu/mainMenu_widget.mainMenu_widget_C:LoadGame",
    "/Game/UI/HUD/W_HUD_LordPanel_V2.W_HUD_LordPanel_V2_C:OnSaveLoaded_Event",
    "/Game/UI/HUD/W_HUD_Timer.W_HUD_Timer_C:setGameSpeed",
    "/Game/UI/HUD/W_HUD_Timer.W_HUD_Timer_C:changeGameSpeed",
    "/Game/UI/HUD/W_HUD_Timer.W_HUD_Timer_C:OnGameSpeedChanged_Event",
    "/Game/UI/HUD/MainUICPP.MainUICPP_C:castAndChangeGameSpeed",
    "/Game/UI/HUD/MainUICPP.MainUICPP_C:time_pause",
    "/Script/ManorLords.TemporalComponent:UpdateDateAndSeason",
    "/Game/CPP_BP/MyPawnCPP_BP3.MyPawnCPP_BP3_C:stopIntroCinematic",
    "/Game/CPP_BP/MyPawnCPP_BP3.MyPawnCPP_BP3_C:playIntroSweep",
    "/Game/CPP_BP/MyPawnCPP_BP3.MyPawnCPP_BP3_C:Timeline_0__FinishedFunc",
    "/Game/CPP_BP/MyPawnCPP_BP3.MyPawnCPP_BP3_C:Timeline__FinishedFunc",
    "/Game/CPP_BP/MyPawnCPP_BP3.MyPawnCPP_BP3_C:zoomTransition__FinishedFunc",
    "/Game/CPP_BP/MyPawnCPP_BP3.MyPawnCPP_BP3_C:ReceiveBeginPlay",
    "/Game/CPP_BP/MyPawnCPP_BP3.MyPawnCPP_BP3_C:ReceiveRestarted",
    "/Game/CPP_BP/MyPawnCPP_BP3.MyPawnCPP_BP3_C:Start Tutorials if Enabled",
    "/Game/UI/HUD/MainUICPP.MainUICPP_C:fadein_Event_0",
    "/Game/CPP_BP/MyPawnCPP_BP3.MyPawnCPP_BP3_C:InpActEvt_slowSpeed_K2Node_InputActionEvent_3",
    "/Game/CPP_BP/MyPawnCPP_BP3.MyPawnCPP_BP3_C:InpActEvt_fastSpeed_K2Node_InputActionEvent_4",
    "/Game/CPP_BP/MyPawnCPP_BP3.MyPawnCPP_BP3_C:InpActEvt_pause_K2Node_InputActionEvent_1",
    "/Script/ManorLords.PawnCPP:playPopupMessageGUI",
    "/Script/ManorLords.PawnCPP:playEventMessage",
    "/Script/ManorLords.PawnCPP:playEventComplexMessage",
    "/Script/ManorLords.PawnCPP:playAlert",
    "/Script/ManorLords.PawnCPP:playAlertFromTag",
    "/Script/ManorLords.PawnCPP:playMessage",
    "/Script/ManorLords.PawnCPP:playQuestMessage",
    "/Script/ManorLords.PawnCPP:addLog",
    "/Script/ManorLords.PawnCPP:triggerTutorialIfNeeded",
    "/Script/ManorLords.PawnCPP:OnWindowFocusChanged",
    "/Script/ManorLords.PawnCPP:onSavingFinished",
    "/Script/ManorLords.PawnCPP:finishCinematicSequence",
    "/Script/ManorLords.PawnCPP:beginNextQueuedCinematicShot",
    "/Script/ManorLords.PawnCPP:setCinematicMode",
    "/Script/ManorLords.PawnCPP:setMainUIMode",
    "/Script/ManorLords.PawnCPP:playCinematicSequence",
}
local ONCE = { ["/Script/ManorLords.TemporalComponent:UpdateDateAndSeason"] = true }

local T0 = os.clock()
local registered = {}
local fired = {}

local function stamp()
    return string.format("t=%.2f os=%d", os.clock() - T0, os.time())
end

local function readState()
    local ok, text = pcall(function()
        local engine = FindFirstOf("RTSMultiEngineCPP")
        if engine == nil or not engine:IsValid() then return "engine=none" end
        local clock = engine:getGameTimeAdjusted()
        local pawn = engine.playerRef
        local ui = (pawn ~= nil and pawn:IsValid()) and string.format(" uiMode=%s cine=%s cineTime=%s", tostring(pawn.currentUIMode),
            tostring(pawn.cinematicMode), tostring(pawn.bCinematicTime)) or ""
        return string.format("clock=%.3f speed=%s sched=%s isSched=%s beforePause=%s%s", clock, tostring(engine.gameSpeed),
            tostring(engine.gameSpeedScheduled), tostring(engine.isGameSpeedScheduled), tostring(engine.gameSpeedBeforePause), ui)
    end)
    return ok and text or ("state=<" .. tostring(text) .. ">")
end

local function describeArgs(packed)
    local parts = {}
    for i = 1, packed.n do
        local ok, text = pcall(function()
            local value = packed[i]
            if value == nil then return "nil" end
            local inner = value.get and value:get() or value
            if type(inner) == "userdata" then return inner:GetFullName():sub(1, 60) end
            return tostring(inner)
        end)
        parts[#parts + 1] = ok and text or "?"
    end
    return table.concat(parts, ",")
end

local function makeCallback(path, phase)
    return function(ctx, ...)
        local packed = table.pack(...)
        pcall(function()
            fired[path] = (fired[path] or 0) + 1
            if fired[path] > (ONCE[path] and 1 or 12) then return end
            local who = "?"
            local okSelf, name = pcall(function() return ctx:get():GetFullName():sub(1, 70) end)
            if okSelf then who = name end
            log.info(TAG, string.format("HOOK %s %s %s self=%s args=[%s] %s", stamp(), phase, path, who,
                describeArgs(packed), readState()))
        end)
    end
end

local function tryRegister(path)
    local ok, err = pcall(RegisterHook, path, makeCallback(path, "pre"), makeCallback(path, "post"))
    if ok then
        registered[path] = true
        log.info(TAG, "registered " .. path)
    end
    return ok, err
end

local function registerPending()
    for _, path in ipairs(HOOKS) do
        if not registered[path] then tryRegister(path) end
    end
end

local function pendingCount()
    local n = 0
    for _, path in ipairs(HOOKS) do
        if not registered[path] then n = n + 1 end
    end
    return n
end

-- Timeline: log the clock only when it starts, stops, or the speed changes.
local last = { clock = nil, running = nil, speed = nil }

local function sampleClock()
    local engine = FindFirstOf("RTSMultiEngineCPP")
    if engine == nil or not engine:IsValid() then return end
    local ok, clock = pcall(function() return engine:getGameTimeAdjusted() end)
    if not ok or type(clock) ~= "number" then return end
    local okSpeed, speed = pcall(function() return engine.gameSpeed end)
    local running = last.clock ~= nil and math.abs(clock - last.clock) >= 0.001
    local okSched, sched = pcall(function() return tostring(engine.gameSpeedScheduled) .. "/" .. tostring(engine.isGameSpeedScheduled) end)
    local changed = last.clock ~= nil and (running ~= last.running or speed ~= last.speed or sched ~= last.sched)
    if changed then
        log.info(TAG, string.format("TICK %s clock=%.3f running=%s speed=%s sched=%s", stamp(), clock, tostring(running),
            tostring(okSpeed and speed or "?"), tostring(okSched and sched or "?")))
    end
    last.sched = sched
    if last.clock ~= nil then last.running = running end
    last.clock, last.speed = clock, okSpeed and speed or nil
end

-- Widget diff: which widgets appear or disappear. This shows what the game does around the clock restart.
local knownWidgets = {}
local widgetPolls = 0

local function widgetName(widget)
    local ok, name = pcall(function() return widget:GetClass():GetFName():ToString() end)
    return ok and name or "?"
end

local function sampleWidgets()
    local ok, all = pcall(FindAllOf, "UserWidget")
    if not ok or all == nil then return end
    local now = {}
    for _, widget in ipairs(all) do
        if widget:IsValid() then
            local name = widgetName(widget)
            now[name] = (now[name] or 0) + 1
        end
    end
    for name, count in pairs(now) do
        if knownWidgets[name] ~= count then
            log.info(TAG, string.format("WIDGET %s %s count %s -> %d", stamp(), name, tostring(knownWidgets[name]), count))
        end
    end
    for name, count in pairs(knownWidgets) do
        if now[name] == nil then log.info(TAG, string.format("WIDGET %s %s count %d -> gone", stamp(), name, count)) end
    end
    knownWidgets = now
end

log.info(TAG, "loaded; os.clock base " .. T0)
registerPending()
log.info(TAG, "registered at start: " .. (#HOOKS - pendingCount()) .. " of " .. #HOOKS)

local polls = 0
LoopAsync(100, function()
    polls = polls + 1
    ExecuteInGameThread(function()
        pcall(sampleClock)
        if polls % 5 == 0 then pcall(sampleWidgets) end
        if polls % 10 == 0 and pendingCount() > 0 then registerPending() end
    end)
    return false
end)
