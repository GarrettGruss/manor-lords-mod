-- Game access of the vassals feature (M07). Every call runs on the game thread.
local core = require("ManorCore")

local M = {}

local function engine()
    local object = FindFirstOf("RTSMultiEngineCPP")
    if object ~= nil and object:IsValid() then return object end
    return nil
end

function M.current_day()
    local e = engine()
    if e == nil then return nil end
    local ok, value = pcall(function() return e.TemporalComponent.daysTotal end)
    if ok and type(value) == "number" then return math.floor(value) end
    return nil
end

-- The goal setting and the victory status of the game instance. Nil when the instance is not there yet.
function M.setup_state()
    local ok, module = pcall(require, "HarnessGameSetup")
    if not ok then return nil, "HarnessGameSetup is not available: " .. tostring(module) end
    local state = module.game_setup_state()
    if not state.ok then return nil, tostring(state.error) end
    return state
end

function M.set_goal(goal)
    local module = require("HarnessGameSetup")
    local answer = module.game_setup_set_goal({ goal = goal })
    if not answer.ok then return nil, tostring(answer.error) end
    return answer
end

-- The rows of all regions (object name, owner, settled flag, families).
function M.regions()
    local answer = core.regions_state()
    if not answer.ok then return nil, tostring(answer.error) end
    return answer.regions
end

function M.region_row(name)
    local rows, problem = M.regions()
    if rows == nil then return nil, problem end
    for _, row in ipairs(rows) do
        if row.region == name then return row end
    end
    return nil, "no region named " .. tostring(name)
end

-- The player claims a free region: layClaim, then finalizeClaim.
function M.claim_for_player(name)
    local lords = require("HarnessLords")
    local answer = lords.claim_region({ target = 0, region = name, finalize = 1 })
    if not answer.ok then return nil, tostring(answer.error) end
    return answer
end

return M
