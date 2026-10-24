-- Widget code of the feature order_tooltip: edits the rows of the game's Public Order tooltip (spike #422, route B).
-- Everything runs inside pcall in the caller. A failed call leaves the tooltip as the game made it.
local M = {}

local ROW_CLASS = "/Game/UI/Tooltips/approvalFactorWidget.approvalFactorWidget_C"
local COLLAPSED = 1 -- ESlateVisibility.Collapsed
local COLORS = {
    green = { R = 0.35, G = 0.8, B = 0.3, A = 1.0 },
    red = { R = 0.85, G = 0.25, B = 0.2, A = 1.0 },
}

local function paint(block, name)
    block:SetColorAndOpacity({ SpecifiedColor = COLORS[name], ColorUseRule = 0 })
end

local function collapse_children(box)
    for i = 0, box:GetChildrenCount() - 1 do
        local child = box:GetChildAt(i)
        if child ~= nil and child:IsValid() then child:SetVisibility(COLLAPSED) end
    end
end

local function add_row(tip, spec)
    local controller = FindFirstOf("PlayerController")
    local library = StaticFindObject("/Script/UMG.Default__WidgetBlueprintLibrary")
    local made = library:Create(controller, StaticFindObject(ROW_CLASS), controller)
    if made == nil or not made:IsValid() then error("the row widget was not made") end
    -- The row sets its default texts when it joins the list, so the texts are written after the add (spike #422).
    tip.recentFactors_VB:AddChildToVerticalBox(made)
    made.DescriptionText:SetText(FText(spec.text))
    made.ValueText:SetText(FText(spec.value))
    paint(made.ValueText, spec.color)
end

-- Hide the native rows, add one row for each mod term, write the mod order in the header.
-- Returns the number of rows added.
function M.apply(tip, view)
    collapse_children(tip.recentFactors_VB)
    if tip.pastFactors_VB ~= nil then collapse_children(tip.pastFactors_VB) end
    for _, spec in ipairs(view.rows) do add_row(tip, spec) end
    tip.current_sum_txt:SetText(FText(view.header))
    paint(tip.current_sum_txt, view.header_color)
    if tip.none_txt ~= nil then tip.none_txt:SetVisibility(COLLAPSED) end
    return #view.rows
end

-- Texts of the rows now in the list (for the test command). Collapsed rows are skipped.
function M.read_rows(tip)
    local list = {}
    local box = tip.recentFactors_VB
    for i = 0, box:GetChildrenCount() - 1 do
        local child = box:GetChildAt(i)
        if child ~= nil and child:IsValid() and child:GetVisibility() ~= COLLAPSED then
            list[#list + 1] = child.DescriptionText:GetText():ToString() .. " | " .. child.ValueText:GetText():ToString()
        end
    end
    return { header = tip.current_sum_txt:GetText():ToString(), rows = list }
end

return M
