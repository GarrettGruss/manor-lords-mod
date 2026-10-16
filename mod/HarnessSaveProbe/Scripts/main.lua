-- HarnessSaveProbe (spec 24, option B test). It only OBSERVES. It logs each call of the save and load functions
-- with the argument values. It never calls a save or load function. Remove it when the spike ends.
local log = require("HarnessLog")

local TAG = "SaveProbe"
local MAX_ATTEMPTS = 40
local RETRY_MS = 3000

-- Native functions: the class exists at start. Blueprint functions: the class loads later, so they are retried.
local NATIVE = {
    "/Script/ManorLords.PawnCPP:requestSaveFile",
    "/Script/ManorLords.PawnCPP:playSaveFinishedNotif",
    "/Script/ManorLords.MLGameInstance:RequestMenuSave",
    "/Script/ManorLords.MLSaveLoadMenuScreen:OnGameSlotSaved",
    "/Script/ManorLords.IoHandler:SaveGameToSlot",
    "/Script/ManorLords.IoHandler:SaveDataToSlot",
    "/Script/ManorLords.IoHandler:LoadGameFromSlot",
    "/Script/ManorLords.IoHandler:LoadDataFromSlot",
    "/Script/ManorLords.IoHandler:DeleteGameInSlot",
}
local BLUEPRINT = {
    "/Game/CPP_BP/MyPawnCPP_BP3.MyPawnCPP_BP3_C:SaveToDiskWithThumbnail",
    "/Game/CPP_BP/MyPawnCPP_BP3.MyPawnCPP_BP3_C:Request Autosave",
    "/Game/UI/Main_Menu/mainMenu_widget.mainMenu_widget_C:LoadGame",
    "/Game/UI/HUD/W_HUD_LordPanel_V2.W_HUD_LordPanel_V2_C:OnSaveLoaded_Event",
    "/Game/CPP_BP/MyPawnCPP_BP3.MyPawnCPP_BP3_C:ReceiveBeginPlay",
}

local counts = {}

local function describe(param)
    local ok, value = pcall(function() return param:get() end)
    if not ok or value == nil then return "?" end
    if type(value) ~= "userdata" then return tostring(value) end
    local okText, text = pcall(function() return value:ToString() end)
    if okText and type(text) == "string" then return text end
    local okName, name = pcall(function() return value:GetFullName() end)
    if okName then return name end
    return "userdata"
end

local function savefileToLoad()
    local ok, text = pcall(function()
        local instance = FindFirstOf("MLGameInstance")
        if instance == nil or not instance:IsValid() then return "<no instance>" end
        return tostring(instance.savefileToLoad:ToString())
    end)
    return ok and text or "<unreadable>"
end

local function observe(path)
    return function(self, ...)
        counts[path] = (counts[path] or 0) + 1
        local args = {}
        for i = 1, select("#", ...) do args[#args + 1] = describe(select(i, ...)) end
        log.info(TAG, string.format("FIRED %s n=%d args=[%s] savefileToLoad=%s", path, counts[path], table.concat(args, " | "), savefileToLoad()))
    end
end

local function register(path)
    local ok, err = pcall(function() RegisterHook(path, observe(path)) end)
    if ok then log.info(TAG, "hooked " .. path) end
    return ok, err
end

for _, path in ipairs(NATIVE) do
    local ok, err = register(path)
    if not ok then log.warn(TAG, "cannot hook " .. path .. ": " .. tostring(err)) end
end

local pending = {}
for _, path in ipairs(BLUEPRINT) do pending[#pending + 1] = path end
local attempts = 0
LoopAsync(RETRY_MS, function()
    attempts = attempts + 1
    local still = {}
    for _, path in ipairs(pending) do
        if not register(path) then still[#still + 1] = path end
    end
    pending = still
    if #pending == 0 then return true end
    if attempts >= MAX_ATTEMPTS then
        for _, path in ipairs(pending) do log.warn(TAG, "gave up hooking " .. path) end
        return true
    end
    return false
end)
log.info(TAG, "loaded; observe only")

---------------------------------------------------------------------------------------------
-- Test commands for the Tags marker spike (probe-save-tags). They write one Name into a Tags array. They never save.
---------------------------------------------------------------------------------------------
local hasCommands, commands = pcall(require, "HarnessCommands")

local function targetObject(target)
    local engine = FindFirstOf("RTSMultiEngineCPP")
    if engine == nil or not engine:IsValid() then return nil, "engine not found" end
    local player = engine.playerRef
    if target == "pawn" then return player end
    if target == "region" then return player.currentRegion end
    return nil, "unknown target"
end

local function tagNames(object)
    local names = {}
    local tags = object.Tags
    for i = 1, #tags do names[#names + 1] = tags[i]:ToString() end
    return names
end

local function tagAdd(args)
    local object, why = targetObject(args.target)
    if object == nil then return nil, why end
    local before = #object.Tags
    object.Tags[before + 1] = FName(args.marker)
    return { before = before, after = #object.Tags, names = tagNames(object) }
end

local function tagsRead(args)
    local object, why = targetObject(args.target)
    if object == nil then return nil, why end
    return { names = tagNames(object) }
end

if hasCommands then
    local target = { type = "string", required = true }
    commands.register("HarnessSaveProbe.tag_add", tagAdd, { target = target, marker = { type = "string", required = true } })
    commands.register("HarnessSaveProbe.tags_read", tagsRead, { target = target })
end
