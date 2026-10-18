-- Pure rules for the target region of a raid (no game calls).
-- A plunder raid always hits the home region. A subjugation raid tries to take a vassal region.
-- Vassals do not exist yet (M07). Until then the home region stands in as the target (marked stand_in).
local M = {}

-- `vassals` is a list of region names (empty until M07). Returns { region = name, stand_in = bool }.
function M.pick(kind, home, vassals, random)
    if kind ~= "subjugation" then return { region = home, stand_in = false } end
    if #vassals == 0 then return { region = home, stand_in = true } end
    return { region = vassals[random(1, #vassals)], stand_in = false }
end

return M
