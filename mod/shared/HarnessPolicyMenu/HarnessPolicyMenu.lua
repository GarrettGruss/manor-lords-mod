-- HarnessPolicyMenu: show the custom policy menu widget that a pak adds (spec 16, issue #60, option c).
-- Why: the menu layout is a cooked Widget Blueprint in the pak policymenu_P.pak. Lua loads the class, makes one widget and shows it.
-- Rules: call only on the game thread. No save function. The class path is fixed, not taken from the request.

local M = {}

M.CLASS_PATH = "/Game/HarnessMod/WBP_PolicyMenu.WBP_PolicyMenu_C"
M.ASSET_PATH = "/Game/HarnessMod/WBP_PolicyMenu"
M.Z_ORDER = 500

local widget = nil

local function isValid(object)
    if object == nil then return false end
    local ok, valid = pcall(function() return object:IsValid() end)
    return ok and valid == true
end

local function read(fn)
    local ok, value = pcall(fn)
    if ok then return value end
    return nil
end

-- Find the class. The pak asset may not be loaded yet, so load the asset as a second step.
local function findClass()
    local class = StaticFindObject(M.CLASS_PATH)
    if isValid(class) then return class, "found" end
    local notes = {}
    for _, path in ipairs({ M.ASSET_PATH, M.ASSET_PATH .. ".WBP_PolicyMenu", M.CLASS_PATH }) do
        local ok, result = pcall(function() return LoadAsset(path) end)
        local detail = ok and isValid(result) and read(function() return result:GetFullName() end) or "invalid"
        notes[#notes + 1] = path .. " -> " .. tostring(ok) .. " " .. tostring(detail)
        class = StaticFindObject(M.CLASS_PATH)
        if isValid(class) then return class, "loaded asset: " .. table.concat(notes, "; ") end
    end
    local function attempt(label, fn)
        local ok, result = pcall(fn)
        notes[#notes + 1] = label .. " ok=" .. tostring(ok) .. (ok and "" or (" err=" .. tostring(result):sub(1, 120)))
        class = StaticFindObject(M.CLASS_PATH)
        return isValid(class)
    end
    local registry = StaticFindObject("/Script/AssetRegistry.Default__AssetRegistryHelpers")
    local kismet = StaticFindObject("/Script/Engine.Default__KismetSystemLibrary")
    notes[#notes + 1] = "registry helpers valid=" .. tostring(isValid(registry)) .. " kismet valid=" .. tostring(isValid(kismet))
    local data = {
        PackageName = FName("/Game/HarnessMod/WBP_PolicyMenu"), PackagePath = FName("/Game/HarnessMod"),
        AssetName = FName("WBP_PolicyMenu"),
        AssetClassPath = { PackageName = FName("/Script/UMGEditor"), AssetName = FName("WidgetBlueprint") },
    }
    if isValid(registry) and attempt("GetAsset", function() return registry:GetAsset(data) end) then
        return class, "GetAsset: " .. table.concat(notes, "; ")
    end
    local softClass = { AssetPath = { PackageName = FName("/Game/HarnessMod/WBP_PolicyMenu"), AssetName = FName("WBP_PolicyMenu_C") }, SubPathString = "" }
    if isValid(kismet) and attempt("LoadClassAsset_Blocking", function() return kismet:LoadClassAsset_Blocking(softClass) end) then
        return class, "LoadClassAsset_Blocking: " .. table.concat(notes, "; ")
    end
    local control = read(function() return LoadAsset("/Game/ManorLords/Database/DT_Alerts") end)
    notes[#notes + 1] = "control DT_Alerts valid=" .. tostring(isValid(control))
    local blueprint = read(function() return StaticFindObject(M.ASSET_PATH .. ".WBP_PolicyMenu") end)
    notes[#notes + 1] = "blueprint object valid=" .. tostring(isValid(blueprint))
    return nil, "class not found (is the pak policymenu installed?) " .. table.concat(notes, "; ")
end

local function describe()
    if not isValid(widget) then return { alive = false } end
    return {
        alive = true,
        name = read(function() return widget:GetFullName() end),
        in_viewport = read(function() return widget:IsInViewport() end),
        visibility = read(function() return widget:GetVisibility() end),
    }
end

function M.menu_pak_show(request)
    if isValid(widget) then return { ok = false, error = "the pak menu is already shown; call menu_pak_hide first" } end
    local class, how = findClass()
    if not class then return { ok = false, error = how } end
    local library = StaticFindObject("/Script/UMG.Default__WidgetBlueprintLibrary")
    local controller = FindFirstOf("PlayerController")
    if not (isValid(library) and isValid(controller)) then
        return { ok = false, error = "widget library or player controller not found" }
    end
    local made = library:Create(controller, class, controller)
    if not isValid(made) then return { ok = false, error = "WidgetBlueprintLibrary:Create returned no widget" } end
    made:AddToViewport(M.Z_ORDER)
    made:SetPositionInViewport({ X = request.x or 300, Y = request.y or 200 }, false)
    widget = made
    local answer = describe()
    answer.ok, answer.class_how = true, how
    return answer
end

function M.menu_pak_read()
    local answer = describe()
    answer.ok = true
    return answer
end

function M.menu_pak_hide()
    if isValid(widget) then widget:RemoveFromParent() end
    widget = nil
    return { ok = true, alive = false }
end

return M
