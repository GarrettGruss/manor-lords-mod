-- Pure text rules of the tech tree menu (M12 iteration 02). No game calls, so a test can run them.
local M = {}

local MARK = { unlocked = "[x] ", available = "", locked = "", other_path = "" }
local COLOR = {
    unlocked = { R = 0.25, G = 0.7, B = 0.3, A = 1 },
    available = { R = 1, G = 1, B = 1, A = 1 },
    locked = { R = 0.45, G = 0.45, B = 0.45, A = 1 },
    other_path = { R = 0.3, G = 0.12, B = 0.12, A = 1 },
}

function M.color(status) return COLOR[status] or COLOR.locked end

function M.node_label(row)
    return (MARK[row.status] or "") .. row.name
end

-- Three lines: the path, the slots, the effects.
function M.header(view)
    local path = view.path_name and (view.path_name .. " (final)") or "not chosen yet"
    local slots = string.format("Node slots: %d free of %d (settlement level %d)", view.free_slots, view.slots, view.level)
    return { "Path: " .. path, slots, "Effects: " .. view.effects }
end

-- The line above the law buttons.
function M.laws_line(view)
    if view.path_name == nil then return "Laws: choose a path first" end
    return string.format("Laws: %d of %d in force", #M.enacted_names(view), view.max_laws)
end

function M.enacted_names(view)
    local names = {}
    for _, law in ipairs(view.laws) do
        if law.status == "enacted" then names[#names + 1] = law.name end
    end
    return names
end

-- A law button says what a click does: repeal a law in force, enact an open law, or why it is closed.
function M.law_label(law)
    if law.status == "enacted" then return "[in force] " .. law.name .. " (repeal)" end
    if law.status == "available" then return "Enact " .. law.name end
    return law.name .. " (closed)"
end

function M.path_label(path) return "Choose " .. path.name end

-- Pixel position of a node on the canvas from its layout data.
function M.position(layout, step_x, step_y)
    return { X = layout.x * step_x, Y = layout.y * step_y }
end

return M
