-- A Hussite raid as the army of an AI lord that is at war with the player (M03 iteration 02, user decision 2026-10-18).
-- Why: a lord army with a challenge walks to the battlefield marker. The marker is moved to the player manor
-- (run 20261018-035856-248b: the army stood within 1300 units of the manor), and declare peace removes a lord army
-- (run 20261018-015705-ee48). The plunder is done by the mod (raid_behavior), not by the army.
-- The helper modules are the proven harness ones (HarnessLords, HarnessBattlefield). Call only on the game thread.
local core = require("ManorCore")
local border = require("features.invasion.border")

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

-- The spawn point on the map border for a raid on the player manor: { x, y, side, distance, direction, anchor }, or nil and a message.
-- `options` is config.invasion.border. `avoid` (optional { x, y }) is the point of another army that this one should not share.
function M.plan_border(options, avoid)
    local _, battlefield = modules()
    if battlefield == nil or battlefield.battlefield_state == nil then return nil, "HarnessBattlefield is not available" end
    local ok_state, state = pcall(battlefield.battlefield_state, { home = true })
    local anchor = ok_state and state and state.would_anchor or nil
    if anchor == nil then return nil, "no anchor for the border point" end
    local bounds, why = border.read_bounds()
    if bounds == nil then return nil, why end
    local point = border.pick(bounds, anchor, { margin = options.margin, inset = options.inset, min_distance = options.min_spawn_distance,
                                                avoid = avoid, avoid_distance = options.min_spawn_distance })
    point.anchor = { x = anchor.x, y = anchor.y }
    point.direction = border.direction(point.anchor, point, options.north_axis)
    return point
end

-- Squads of the templates (one spawnArmy call each), war, and a challenge whose battlefield stands at the player manor.
-- `at` (optional { x, y }) is the spawn point on the map border; without it the squads start `settings.start_dy` from the player pawn.
-- Returns true and { lord, anchor = {x, y}, squads = {{ id, template }}, home_region, at } or false and a message.
-- A failure after some squads were spawned returns a third value, true: armies are on the map, so the caller must not add
-- bandit squads on top. The partial army is sent away with peace.
function M.start(templates, settings, at)
    local ok, problem, spawned = M.start_checked(templates, settings, at)
    if not ok and spawned then
        local peace_ok, peace_problem = M.peace()
        core.log.error(TAG, string.format("lord raid failed after a partial spawn (%s); peace=%s%s", tostring(problem), tostring(peace_ok),
            peace_ok and "" or (" problem=" .. tostring(peace_problem))))
    end
    return ok, problem, spawned
end

function M.start_checked(templates, settings, at)
    local lords, battlefield = modules()
    if lords == nil then return false, battlefield end
    local ok, problem = ensure_lord(lords, settings.lord_name)
    if not ok then return false, problem end
    ok, problem = step("lord_declare_war", lords.lord_declare_war({ lord = lord_number, target = 0 }))
    if not ok then return false, problem end
    local squads = {}
    for _, template in ipairs(templates) do
        local request = { lord = lord_number, template = template, count = 1, dx = 0, dy = settings.start_dy }
        if at ~= nil then request.x, request.y = at.x, at.y end
        local answer = lords.lord_spawn_army(request)
        ok, problem = step("lord_spawn_army " .. template, answer)
        if not ok then return false, problem, #squads > 0 end
        squads[#squads + 1] = { id = answer.squads and answer.squads[1] or false, template = template }
    end
    local home = core.player_region()
    local anchored = battlefield.battlefield_anchor({ lord = lord_number, home = true })
    ok, problem = step("battlefield_anchor", anchored)
    if not ok then return false, problem, #squads > 0 end
    ok, problem = step("challenge", anchored.challenge)
    if not ok then return false, problem, #squads > 0 end
    return true, { lord = lord_number, anchor = anchored.anchor, squads = squads,
                   home_region = home and core.region_row(home).region or nil, at = at }
end

-- The pawn of the raid lord (a test command writes the region owner with it), or nil.
function M.lord_pawn()
    local lords = modules()
    if lords == nil or lord_number == nil then return nil end
    return lords.pawn_by_number(lord_number)
end

-- Peace removes the army of the lord (about 60 game seconds).
function M.peace()
    local lords = modules()
    if lords == nil or lord_number == nil then return false, "no raid lord" end
    return step("lord_declare_peace", lords.lord_declare_peace({ lord = lord_number, target = 0 }))
end

core.log.info(TAG, "lord_raid loaded")
return M
