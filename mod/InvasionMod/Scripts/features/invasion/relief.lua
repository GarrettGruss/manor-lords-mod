-- The relief army of the liege: squads under the control of the player (M02 iteration 06, decisions 1 and 26).
-- spawnArmy with the player pawn as owner gives side "player" (spike S7). Call only on the game thread.
local M = {}

-- Spawns one squad for each template at the spot. Returns true, or false and a message.
function M.spawn(templates, spot)
    if #templates == 0 then return true end
    local engine = FindFirstOf("RTSMultiEngineCPP")
    if engine == nil or not engine:IsValid() then return false, "no RTSMultiEngineCPP" end
    local owner = engine.playerRef
    if owner == nil or not owner:IsValid() then return false, "no player pawn" end
    local names = {}
    for index, name in ipairs(templates) do names[index] = FName(name) end
    local ok, problem = pcall(function() return engine:spawnArmy({ X = spot.x, Y = spot.y, Z = spot.z }, names, owner, 0, 0) end)
    if not ok then return false, "spawnArmy: " .. tostring(problem) end
    return true
end

return M
