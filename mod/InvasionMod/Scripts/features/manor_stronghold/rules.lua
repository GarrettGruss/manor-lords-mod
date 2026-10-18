-- Pure rules of the manor stronghold feature (M13). No game access.
local M = {}

-- Capacity of one manor module in units of goods. The bonus comes from the tech tree.
function M.storage_capacity(base, bonus)
    return math.max(0, math.floor(base + (bonus or 0)))
end

return M
