-- Pure rules of the raid tracker (no game calls), so a test can run them without a game.
local M = {}

-- A new raid record. `units` maps a unit key to { loot, x, y }. A unit has no loot and no place until it is seen.
function M.new_raid(id, start_day, squads, unit_keys)
    local units, living = {}, 0
    for _, key in ipairs(unit_keys) do
        units[key] = { loot = 0, x = nil, y = nil }
        living = living + 1
    end
    return {
        id = id, start_day = start_day, squads = squads, units = units, initial = living, living = living,
        deaths = 0, departures = 0, carried_out = 0, returned = 0, lost = 0, capped = 0, peak_loot = 0,
        burned = 0, leaving = false, state = living > 0 and "active" or "empty", end_day = nil,
    }
end

-- Loot above the carry cap is cut to the cap. Returns the new value and whether it was cut.
function M.clamp_carry(loot, cap)
    if loot > cap then return cap, true end
    return loot, false
end

function M.total_loot(raid)
    local total = 0
    for _, unit in pairs(raid.units) do total = total + unit.loot end
    return total
end

-- A unit that is gone and was last seen at or below `exit_y` walked off the map. Any other missing unit died.
function M.departure_kind(unit, exit_y)
    if unit.y ~= nil and unit.y <= exit_y then return "left" end
    return "died"
end

-- Apply one look at the world. `seen` maps a unit key to { loot, x, y, dead } for the units the game still lists.
-- A tracked unit that is not seen, or is dead, is gone. Returns the death events: { key, loot, x, y }.
-- `config` has carry_cap and exit_y. `seen[key].new_loot` is the loot cut to the cap (the caller writes it back).
function M.update(raid, seen, config, day)
    local deaths = {}
    for key, unit in pairs(raid.units) do
        local now = seen[key]
        if now ~= nil and not now.dead then
            local loot, cut = M.clamp_carry(now.loot or 0, config.carry_cap)
            if cut then raid.capped = raid.capped + 1 end
            now.new_loot = loot
            unit.loot, unit.x, unit.y = loot, now.x or unit.x, now.y or unit.y
        else
            if now ~= nil then unit.x, unit.y = now.x or unit.x, now.y or unit.y end
            raid.units[key] = nil
            raid.living = raid.living - 1
            local died_in_view = now ~= nil and now.dead
            if not died_in_view and M.departure_kind(unit, config.exit_y) == "left" then
                raid.departures = raid.departures + 1
                raid.carried_out = raid.carried_out + unit.loot
            else
                raid.deaths = raid.deaths + 1
                deaths[#deaths + 1] = { key = key, loot = unit.loot, x = unit.x, y = unit.y }
            end
        end
    end
    raid.peak_loot = math.max(raid.peak_loot, M.total_loot(raid))
    if raid.state == "active" and raid.living == 0 then
        raid.state = raid.departures > 0 and "left" or "destroyed"
        raid.end_day = day
    end
    return deaths
end

-- All goods the raid took so far: carried now, carried off the map, returned to a store, or lost.
function M.looted_total(raid)
    return M.total_loot(raid) + raid.carried_out + raid.returned + raid.lost
end

function M.record_return(raid, amount) raid.returned = raid.returned + amount end
function M.record_loss(raid, amount) raid.lost = raid.lost + amount end

-- The store that is nearest to a place. `stores` is a list of { x, y, ... }. Returns nil for an empty list.
function M.nearest_store(stores, x, y)
    local best, best_distance
    for _, store in ipairs(stores) do
        local distance = (store.x - x) ^ 2 + (store.y - y) ^ 2
        if best_distance == nil or distance < best_distance then best, best_distance = store, distance end
    end
    return best
end

-- The good that the store holds most of. A store with no goods gets the fallback good.
function M.pick_good(by_good, fallback)
    local best, best_amount = nil, 0
    for good, amount in pairs(by_good) do
        if amount > best_amount or (amount == best_amount and best ~= nil and good < best) then best, best_amount = good, amount end
    end
    return best or fallback
end

-- The numbers that the command and the log show.
function M.summary(raid)
    return {
        id = raid.id, start_day = raid.start_day, end_day = raid.end_day, squads = raid.squads, state = raid.state,
        initial = raid.initial, living = raid.living, deaths = raid.deaths, departures = raid.departures,
        loot = M.total_loot(raid), looted_total = M.looted_total(raid), carried_out = raid.carried_out, peak_loot = raid.peak_loot, returned = raid.returned, lost = raid.lost,
        capped = raid.capped, burned = raid.burned, leaving = raid.leaving,
    }
end

return M
