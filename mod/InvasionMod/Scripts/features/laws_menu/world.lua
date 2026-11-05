-- Game reads of the Laws menu (change add-laws-menu). Game objects are touched on the game thread only.
local core = require("ManorCore")
local isValid, read = core.isValid, core.read
local M = {}

-- The day of the calendar year (TemporalComponent.day), for the days to the start of spring.
function M.day_of_year()
    local engine = FindFirstOf("RTSMultiEngineCPP")
    if not isValid(engine) then return nil end
    local day = read(function() return engine.TemporalComponent.day end)
    return type(day) == "number" and math.floor(day) or nil
end

return M
