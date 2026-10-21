-- HarnessTexProbe: spike helper for custom menu pictures (change spike-menu-custom-textures, #333).
-- One command, texture_probe, with an `action`: load_png, show, box, close. Each step is logged and returns what worked.
-- Why a ladder of pcall steps: it is not known yet which UMG calls UE4SS can make. The answer says which step failed.
-- Rules: game thread only. No save function. No Lua string goes to an FName argument of a widget function (CLAUDE.md, Safety).
-- Nothing here reads the Brush struct back: reads of struct fields with soft objects can crash the game.
local log = require("HarnessLog")

local M = {}
local TAG = "HarnessTexProbe"
local S = { texture = nil, widget = nil, image = nil, steps = {} }

local function isValid(object)
    if object == nil then return false end
    local ok, valid = pcall(function() return object:IsValid() end)
    return ok and valid == true
end

local function step(name, fn)
    local ok, value = pcall(fn)
    local text = ok and "ok" or tostring(value)
    log.info(TAG, name .. ": " .. text)
    S.steps[#S.steps + 1] = { name = name, ok = ok, error = (not ok) and text or nil }
    if ok then return value, true end
    return nil, false
end

local function reflected(path)
    local object = StaticFindObject(path)
    return isValid(object) and object or nil
end

local function checkPath(path)
    if type(path) ~= "string" or not path:lower():match("%.png$") then return nil, "path must end with .png" end
    if path:find("..", 1, true) then return nil, "path must not contain .." end
    return (path:gsub("\\", "/"))
end

local function controller()
    return FindFirstOf("PlayerController")
end

-- Candidate 2: KismetRenderingLibrary:ImportFileAsTexture2D(WorldContextObject, Filename) -> Texture2D
local function load_png(request)
    local path, problem = checkPath(request.path)
    if not path then return { ok = false, error = problem } end
    S.steps = {}
    local library = reflected("/Script/Engine.Default__KismetRenderingLibrary")
    if not library then return { ok = false, error = "KismetRenderingLibrary not found" } end
    local texture = step("ImportFileAsTexture2D", function() return library:ImportFileAsTexture2D(controller(), path) end)
    if not isValid(texture) then return { ok = false, error = "no texture returned", steps = S.steps } end
    S.texture = texture
    local width = step("GetSizeX", function() return texture:Blueprint_GetSizeX() end)
    local height = step("GetSizeY", function() return texture:Blueprint_GetSizeY() end)
    return { ok = true, width = width, height = height, steps = S.steps }
end

-- A UserWidget made from the C++ class has no widget tree. The probe builds one and makes an Image the root.
local function build_widget()
    local userClass = reflected("/Script/UMG.UserWidget")
    local library = reflected("/Script/UMG.Default__WidgetBlueprintLibrary")
    if not (userClass and library) then return nil, "UserWidget class or WidgetBlueprintLibrary not found" end
    local widget = step("WidgetBlueprintLibrary:Create", function() return library:Create(controller(), userClass, controller()) end)
    if not isValid(widget) then return nil, "no widget" end
    local tree = step("construct WidgetTree", function()
        return StaticConstructObject(StaticFindObject("/Script/UMG.WidgetTree"), widget, FName("ProbeTree"))
    end)
    if not isValid(tree) then return nil, "no widget tree" end
    step("set WidgetTree", function() widget.WidgetTree = tree end)
    local image = step("construct Image", function()
        return StaticConstructObject(StaticFindObject("/Script/UMG.Image"), tree, FName("ProbeImage"))
    end)
    if not isValid(image) then return nil, "no image" end
    step("set RootWidget", function() tree.RootWidget = image end)
    S.widget, S.image = widget, image
    return widget
end

local function close()
    if isValid(S.widget) then step("RemoveFromParent", function() S.widget:RemoveFromParent() end) end
    S.widget, S.image = nil, nil
    return { ok = true }
end

local function show(request)
    if not isValid(S.texture) then return { ok = false, error = "load_png first" } end
    close()
    S.steps = {}
    local widget, problem = build_widget()
    if not widget then return { ok = false, error = problem, steps = S.steps } end
    step("SetBrushFromTexture", function() S.image:SetBrushFromTexture(S.texture, false) end)
    local width, height = tonumber(request.width) or 1280, tonumber(request.height) or 720
    step("SetDesiredSizeOverride", function() S.image:SetDesiredSizeOverride({ X = width, Y = height }) end)
    step("AddToViewport", function() widget:AddToViewport(100) end)
    step("SetPositionInViewport", function() widget:SetPositionInViewport({ X = 0, Y = 0 }, false) end)
    local inViewport = step("IsInViewport", function() return widget:IsInViewport() end)
    return { ok = true, in_viewport = inViewport, steps = S.steps }
end

-- 9-slice: DrawAs Box (1) with a normalized Margin, then a size. Brush fields are written only, never read.
local function box(request)
    if not isValid(S.image) then return { ok = false, error = "show first" } end
    S.steps = {}
    local margin = tonumber(request.margin) or 0.0625 -- 16 of 256 px
    local width, height = tonumber(request.width) or 400, tonumber(request.height) or 300
    step("Brush.DrawAs = Box", function() S.image.Brush.DrawAs = 1 end)
    step("Brush.Margin", function() S.image.Brush.Margin = { Left = margin, Top = margin, Right = margin, Bottom = margin } end)
    step("SetDesiredSizeOverride", function() S.image:SetDesiredSizeOverride({ X = width, Y = height }) end)
    step("SetPositionInViewport", function() S.widget:SetPositionInViewport({ X = 100, Y = 100 }, false) end)
    return { ok = true, width = width, height = height, steps = S.steps }
end

function M.texture_probe(request)
    local action = request.action
    if action == "load_png" then return load_png(request) end
    if action == "show" then return show(request) end
    if action == "box" then return box(request) end
    if action == "close" then return close() end
    return { ok = false, error = "action must be load_png, show, box or close" }
end

return M
