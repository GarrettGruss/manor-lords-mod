-- Game access of the tech tree feature (M12). Every call runs on the game thread.
local core = require("ManorCore")

local M = {}

function M.settlement_level()
    local region = core.player_region()
    if region == nil then return nil end
    local ok, value = pcall(function() return region.settlementLevel end)
    if ok and type(value) == "number" then return math.floor(value) end
    return nil
end

-- The squads the player commands. TBD: this is the count that "garrison" means for Fear of the Lord (M13 may refine it).
function M.garrison_squads()
    local engine = FindFirstOf("RTSMultiEngineCPP")
    if engine == nil or not engine:IsValid() then return nil end
    local ok, value = pcall(function() return engine.playerRef.commandedSquads:GetArrayNum() end)
    if ok and type(value) == "number" then return value end
    return nil
end

-- The data folder lies next to the Scripts folder of the mod. UE4SS puts that Scripts folder on package.path.
function M.data_path(relative)
    for entry in string.gmatch(package.path, "[^;]+") do
        local scripts = entry:gsub("\\", "/"):match("^(.*)/Scripts/%?%.lua$")
        if scripts and scripts:find("InvasionMod", 1, true) then return scripts .. "/" .. relative end
    end
    error("tech tree: the Scripts folder of the mod is not on package.path", 0)
end

return M
