-- A Hussite raid as the army of an AI lord that is at war with the player (M03 iteration 02, user decision 2026-10-18).
-- Why: a lord army with a challenge walks to the battlefield marker. The marker is moved to the player manor
-- (run 20261018-035856-248b: the army stood within 1300 units of the manor), and declare peace removes a lord army
-- (run 20261018-015705-ee48). The plunder is done by the mod (raid_behavior), not by the army.
-- The helper modules are the proven harness ones (HarnessLords, HarnessBattlefield). Call only on the game thread.
local core = require("ManorCore")

local TAG = "InvasionMod.lord_raid"
local M = {}

local lord_number = nil -- the raid lord of this Lua state

local function modules()
    local ok_lords, lords = pcall(require, "HarnessLords")
    local ok_field, battlefield = pcall(require, "HarnessBattlefield")
    if not ok_lords or not ok_field then return nil, "HarnessLords or HarnessBattlefield is not available" end
    return lords, battlefield
end

local function step(label, answer)
    if answer == nil or answer.ok ~= true then return false, label .. ": " .. tostring(answer and answer.error) end
    return true
end

local function ensure_lord(lords, name)
    if lord_number ~= nil and core.isValid(lords.pawn_by_number(lord_number)) then return true end
    local made = lords.spawn_ai_lord({ name = name })
    local ok, problem = step("spawn_ai_lord", made)
    if not ok then return false, problem end
    lord_number = made.lord
    for _, call in ipairs({
        { "lord_relations", function() return lords.lord_relations({ lord = lord_number }) end },
        { "lord_start_ai", function() return lords.lord_start_ai({ lord = lord_number, value = 1, build = 0 }) end },
    }) do
        ok, problem = step(call[1], call[2]())
        if not ok then return false, problem end
    end
    return true
end

-- Squads of the templates (one spawnArmy call each), war, and a challenge whose battlefield stands at the player manor.
-- Returns true and { lord, anchor = {x, y}, squads = {{ id, template }}, home_region } or false and a message.
function M.start(templates, settings)
    local lords, battlefield = modules()
    if lords == nil then return false, battlefield end
    local ok, problem = ensure_lord(lords, settings.lord_name)
    if not ok then return false, problem end
    ok, problem = step("lord_declare_war", lords.lord_declare_war({ lord = lord_number, target = 0 }))
    if not ok then return false, problem end
    local squads = {}
    for _, template in ipairs(templates) do
        local answer = lords.lord_spawn_army({ lord = lord_number, template = template, count = 1, dx = 0, dy = settings.start_dy })
        ok, problem = step("lord_spawn_army " .. template, answer)
        if not ok then return false, problem end
        squads[#squads + 1] = { id = answer.squads and answer.squads[1] or false, template = template }
    end
    local home = core.player_region()
    local anchored = battlefield.battlefield_anchor({ lord = lord_number })
    ok, problem = step("battlefield_anchor", anchored)
    if not ok then return false, problem end
    ok, problem = step("challenge", anchored.challenge)
    if not ok then return false, problem end
    return true, { lord = lord_number, anchor = anchored.anchor, squads = squads,
                   home_region = home and core.region_row(home).region or nil }
end

-- Peace removes the army of the lord (about 60 game seconds).
function M.peace()
    local lords = modules()
    if lords == nil or lord_number == nil then return false, "no raid lord" end
    return step("lord_declare_peace", lords.lord_declare_peace({ lord = lord_number, target = 0 }))
end

core.log.info(TAG, "lord_raid loaded")
return M
