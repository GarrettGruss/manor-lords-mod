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
    return { text = text, value = signed(value), color = value >= 0 and M.GREEN or M.RED, up = value >= 0 }
end

-- A text item below the rows: { label, value, text, color }. The widget shows `text` alone, or `label` and `value` as in a row.
local function note(label, value)
    return { label = label, value = value, text = label .. " " .. value, color = M.RED }
end

local function days_text(days)
    if days == 1 then return "1 day" end
    return string.format("%d days", days)
end

-- terms.revolt: nil (no timer) or { days, blocked }. Returns the text items: the counter, then the blocked item (only when blocked).
function M.notes(revolt)
    local list = {}
    if revolt == nil then return list end
    if revolt.days <= 0 then
        list[1] = { label = "Peasants revolt", value = "today", text = "Peasants revolt today", color = M.RED }
    else
        list[1] = note("Peasants revolt in", days_text(revolt.days))
    end
    if revolt.blocked ~= nil then
        list[2] = { label = "Revolt blocked", value = revolt.blocked, text = "Revolt blocked: " .. revolt.blocked, color = M.RED }
    end
    return list
end

-- Returns nil when there is no mod order (the tooltip then stays native), else { header, header_color, rows, notes }.
-- A row is { text, value, color, up }: the value text has a sign, the colour is "green" or "red" as in the game.
function M.build(terms)
    if terms == nil or type(terms.order) ~= "number" then return nil end
    local rows = {}
    -- No Manor row without a built manor (term 0). Terms are nil before the first tick.
    if (terms.manor_term or 0) ~= 0 then rows[#rows + 1] = row("Manor", terms.manor_term) end
    if (terms.homeless_term or 0) > 0 then rows[#rows + 1] = row("Homeless families", -terms.homeless_term) end
    if (terms.leave_gain or 0) ~= 0 then rows[#rows + 1] = row("Peasants revolted", terms.leave_gain) end
    return { header = string.format("%d%%", terms.order), header_color = terms.order >= 0 and M.GREEN or M.RED, rows = rows,
        notes = M.notes(terms.revolt) }
end

return M
