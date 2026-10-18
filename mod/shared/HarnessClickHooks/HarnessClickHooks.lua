-- HarnessClickHooks: event-driven button clicks for pak widgets (spec 34).
-- Why: a cooked Widget Blueprint of ours has no graph, so a Button inside it has no hookable click.
-- WBP_ClickButton (pak file from ue/make_click_button.py) has a graph. Its Button01 OnClicked event is a UFunction that the game
-- calls through ProcessEvent, so RegisterHook sees it. One hook serves every instance.
-- Use: a menu widget has a Border where a button belongs. attach() puts a click button into the Border. The caller drains
-- the clicks from its scheduler tick (the hook only pushes to a queue; no game call runs inside the hook).
-- Notes: docs/harness/34-widget-click-hooks/README.md.
local M = {}

local PACKAGE_PATH, ASSET_NAME = "/Game/HarnessMod", "WBP_ClickButton"
local CLASS_PATH = PACKAGE_PATH .. "/" .. ASSET_NAME .. "." .. ASSET_NAME .. "_C"
local EVENT_PATH = CLASS_PATH .. ":BndEvt__Button01_K2Node_ComponentBoundEvent_0_OnButtonClickedEvent__DelegateSignature"

local handles = {} -- full name of the click widget -> handle
local queue = {}
local hooked = false

local function valid(object)
    return object ~= nil and object:IsValid()
end

local function full_name_of(object)
    local ok, name = pcall(function() return object:GetFullName() end)
    return ok and name or nil
end

-- LoadAsset does not load an asset of a mod pak. The asset registry call does (spec 16 pak-widget-spike.md).
local function find_class()
    local found = StaticFindObject(CLASS_PATH)
    if valid(found) then return found end
    local registry = StaticFindObject("/Script/AssetRegistry.Default__AssetRegistryHelpers")
    if not valid(registry) then return nil, "AssetRegistryHelpers not found" end
    local data = {
        PackageName = FName(PACKAGE_PATH .. "/" .. ASSET_NAME), PackagePath = FName(PACKAGE_PATH), AssetName = FName(ASSET_NAME),
        AssetClassPath = { PackageName = FName("/Script/UMGEditor"), AssetName = FName("WidgetBlueprint") },
    }
    local ok, err = pcall(function() return registry:GetAsset(data) end)
    if not ok then return nil, "GetAsset: " .. tostring(err) end
    found = StaticFindObject(CLASS_PATH)
    if not valid(found) then return nil, "class not found; is the pak with WBP_ClickButton installed?" end
    return found
end

local function install_hook()
    if hooked then return true end
    local ok, err = pcall(RegisterHook, EVENT_PATH, function(self)
        queue[#queue + 1] = { name = full_name_of(self:get()), at = os.clock() }
    end)
    if not ok then return false, "RegisterHook: " .. tostring(err) end
    hooked = true
    return true
end

-- Puts a click button into a Border. `tag` comes back in the click record. Returns a handle or nil and a message.
function M.attach(border, controller, tag)
    local class, problem = find_class()
    if not class then return nil, problem end
    local installed, hook_problem = install_hook()
    if not installed then return nil, hook_problem end
    local library = StaticFindObject("/Script/UMG.Default__WidgetBlueprintLibrary")
    local widget = library:Create(controller, class, controller)
    if not valid(widget) then return nil, "WidgetBlueprintLibrary:Create returned no click button" end
    border:SetContent(widget)
    local handle = { widget = widget, tag = tag, name = full_name_of(widget), widget_name = widget:GetFName():ToString() }
    handles[handle.name] = handle
    return handle
end

-- Finds the label of each handle. Button01 is a variable of the click button (its OnClicked event needs it). The label is
-- Button01 > HorizontalContentBox > child 1 (TextBorder) > ValueText. This avoids a scan of all text blocks (FindAllOf), which
-- was slow and crashed the game. Call it once after the attach calls of a menu. Returns true, or false and a message.
function M.bind_texts(list)
    for _, handle in ipairs(list) do
        local ok, text = pcall(function()
            return handle.widget.Button01:GetContent():GetChildAt(1):GetContent()
        end)
        if not (ok and valid(text)) then return false, "the label of a click button was not found: " .. tostring(text) end
        handle.text = text
    end
    return true
end

function M.set_text(handle, text)
    if handle.shown == text then return end -- a game call for each label and tick caused Lua state corruption
    handle.shown = text
    handle.text:SetText(FText(text))
end

function M.set_visible(handle, shown)
    if valid(handle.widget) then handle.widget:SetVisibility(shown and 0 or 1) end -- ESlateVisibility: Visible, Collapsed
end

-- Forget the handles of a closed menu.
function M.release(list)
    for _, handle in ipairs(list) do handles[handle.name] = nil end
end

-- Returns the handles of `owner` (the owner field of the tag) clicked since the last call, oldest first.
-- Several features of one mod share the queue. Clicks of other owners stay in it. A handle appears twice for two clicks.
function M.drain(owner)
    local clicked, rest = {}, {}
    for _, record in ipairs(queue) do
        local handle = record.name and handles[record.name]
        if handle == nil then
            -- the widget was released: drop the click
        elseif handle.tag.owner == owner then
            clicked[#clicked + 1] = handle
        else
            rest[#rest + 1] = record
        end
    end
    queue = rest
    return clicked
end

return M
