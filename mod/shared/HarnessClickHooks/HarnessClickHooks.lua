-- HarnessClickHooks: event-driven button clicks for pak widgets (spec 34).
-- A cooked button widget (WBP_ClickButton) has a Blueprint graph with an OnClicked event. That event is a
-- UFunction called through ProcessEvent, so RegisterHook sees it. One hook serves every instance.
-- The hook callback only pushes the instance into a queue. The caller drains the queue from its scheduler tick.
local M = {}

local CLASS_PATH = "/Game/HarnessMod/WBP_ClickButton.WBP_ClickButton_C"
local PACKAGE_PATH, ASSET_NAME = "/Game/HarnessMod", "WBP_ClickButton"
local EVENT_PATH = CLASS_PATH .. ":BndEvt__Button01_K2Node_ComponentBoundEvent_0_OnButtonClickedEvent__DelegateSignature"

local queue = {}
local hooked = false

-- LoadAsset does not load an asset of a mod pak. The asset registry call does (spec 16 pak-widget-spike.md).
function M.find_class()
    local found = StaticFindObject(CLASS_PATH)
    if found and found:IsValid() then return found end
    local registry = StaticFindObject("/Script/AssetRegistry.Default__AssetRegistryHelpers")
    if not (registry and registry:IsValid()) then return nil, "AssetRegistryHelpers not found" end
    local data = {
        PackageName = FName(PACKAGE_PATH .. "/" .. ASSET_NAME), PackagePath = FName(PACKAGE_PATH), AssetName = FName(ASSET_NAME),
        AssetClassPath = { PackageName = FName("/Script/UMGEditor"), AssetName = FName("WidgetBlueprint") },
    }
    local ok, err = pcall(function() return registry:GetAsset(data) end)
    if not ok then return nil, "GetAsset: " .. tostring(err) end
    found = StaticFindObject(CLASS_PATH)
    if not (found and found:IsValid()) then return nil, "class not found; is the click button pak installed?" end
    return found
end

function M.install_hook()
    if hooked then return true end
    local ok, err = pcall(RegisterHook, EVENT_PATH, function(self)
        local widget = self:get()
        queue[#queue + 1] = { widget = widget, at = os.clock() }
    end)
    if not ok then return false, tostring(err) end
    hooked = true
    return true
end

-- Returns the click records since the last call: { { widget = <UserWidget>, at = <os.clock> }, ... }.
function M.drain()
    local taken = queue
    queue = {}
    return taken
end

function M.new_button(controller)
    local class, problem = M.find_class()
    if not class then return nil, problem end
    local installed, hook_problem = M.install_hook()
    if not installed then return nil, hook_problem end
    local library = StaticFindObject("/Script/UMG.Default__WidgetBlueprintLibrary")
    local made = library:Create(controller, class, controller)
    if not (made and made:IsValid()) then return nil, "WidgetBlueprintLibrary:Create returned no widget" end
    return made
end

return M
