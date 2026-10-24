-- Pure row builder of the feature order_tooltip. No game access, so the fake game and plain Lua can test it.
-- terms (from bandits.order_terms): order, manor_term, homeless_term, leave_gain. Terms are nil before the first tick.
local M = {}

M.GREEN = "green"
M.RED = "red"

local function signed(value)
    if value >= 0 then return string.format("+%d", value) end
    return string.format("-%d", -value)
end

local function row(text, value)
    return { text = text, value = signed(value), color = value >= 0 and M.GREEN or M.RED }
end

-- Returns nil when there is no mod order (the tooltip then stays native), else { header, rows }.
-- A row is { text, value, color }: the value text has a sign, the colour is "green" or "red" as in the game.
function M.build(terms)
    if terms == nil or type(terms.order) ~= "number" then return nil end
    local rows = {}
    if terms.manor_term ~= nil then
        rows[#rows + 1] = row("Manor", terms.manor_term)
        if (terms.homeless_term or 0) > 0 then rows[#rows + 1] = row("Homeless families", -terms.homeless_term) end
    end
    if (terms.leave_gain or 0) ~= 0 then rows[#rows + 1] = row("Left for banditry", terms.leave_gain) end
    return { header = string.format("%d%%", terms.order), header_color = terms.order >= 0 and M.GREEN or M.RED, rows = rows }
end

return M
