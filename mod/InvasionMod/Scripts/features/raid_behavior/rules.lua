-- Pure rules of the raid tracker (no game calls), so a test can run them without a game.
local M = {}

-- A new raid record. `units` maps a unit key to { loot, x, y }. A unit has no loot and no place until it is seen.
function M.new_raid(id, start_day, squads, unit_keys, roles, lord)
    local units, living = {}, 0
    for _, key in ipairs(unit_keys) do
        units[key] = { loot = 0, x = nil, y = nil }
        living = living + 1
    end
    return {
        id = id, start_day = start_day, squads = squads, units = units, initial = living, living = living,
        deaths = 0, departures = 0, carried_out = 0, returned = 0, lost = 0, capped = 0, peak_loot = 0,
        burned = 0, leaving = false, roles = roles == true, lord = lord, marching = lord ~= nil and lord.marching == true, spawn_day = start_day, arrival_day = nil, plundered = 0, plunder_goods = {}, unpaid = 0, last_plunder_day = nil, stolen = 0, last_steal_day = nil, leave_reason = nil, state = living > 0 and "active" or "empty", end_day = nil,
    }
end

-- The raid type: "hussite" for a lord army, "bandit" for the bandit squads of a role raid, nil for a native raid (type unknown).
function M.raid_type(raid)
    if raid.lord ~= nil then return "hussite" end
    if raid.roles then return "bandit" end
    return nil
end

-- The loot goal for each raider at the start: `carry_cap` for a Hussite raid, `leave.loot_per_raider` for any other role raid.
function M.loot_goal(raid, leave, carry_cap)
    if raid.lord ~= nil and carry_cap ~= nil then return carry_cap end
    return leave.loot_per_raider
end

-- Loot above the carry cap is cut to the cap (Hussite raids only). Returns the new value and whether it was cut.
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
-- A tracked unit that is not seen, or is dead (the reader also marks a unit that the census no longer counts), is gone. Returns the death events: { key, loot, x, y }.
-- `config` has carry_cap and exit_y. `seen[key].new_loot` is the loot cut to the cap (the caller writes it back).
function M.update(raid, seen, config, day)
    local deaths = {}
    local cap = raid.lord ~= nil and config.carry_cap or nil -- the game manages the loot of every other raid
    raid.carry_cap = cap
    for key, unit in pairs(raid.units) do
        local now = seen[key]
        if now ~= nil and not now.dead then
            local loot = now.loot or 0
            if cap ~= nil then
                local cut
                loot, cut = M.clamp_carry(loot, cap)
                if cut then raid.capped = raid.capped + 1 end
                now.new_loot = loot
            end
            unit.loot, unit.x, unit.y = loot, now.x or unit.x, now.y or unit.y
        else
            if now ~= nil then unit.x, unit.y = now.x or unit.x, now.y or unit.y end
            raid.units[key] = nil
            raid.living = raid.living - 1
            local died_in_view = now ~= nil and now.dead
            if unit.exiting then
                raid.departures = raid.departures + 1
            elseif not died_in_view and M.departure_kind(unit, config.exit_y) == "left" then
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
    return M.total_loot(raid) + raid.carried_out + raid.returned + raid.lost + raid.plundered
end

-- Why a role raid must leave now, or nil. Only role raids (spawnArmy) are checked: native raids leave on their own.
-- `leave` has loot_per_raider, loss_share and max_days. Loot taken counts what raiders carry, returned and carried out.
function M.is_subjugation(raid)
    return raid.lord ~= nil and (raid.lord.kind == "subjugation" or raid.lord.kind == "great") -- both stay until beaten
end

function M.leave_reason(raid, day, leave, carry_cap)
    if raid.marching then return nil end -- the raid starts at arrival (change update-spawn-from-map-border)
    if not raid.roles or raid.state ~= "active" or raid.leave_reason ~= nil or raid.leaving or raid.initial < 1 then return nil end
    if M.is_subjugation(raid) then return nil end -- a subjugation raid stays until it is beaten or wins (M02.03)
    if M.looted_total(raid) >= M.loot_goal(raid, leave, carry_cap) * raid.initial then return "loot" end
    if raid.deaths / raid.initial >= leave.loss_share then return "losses" end
    if day ~= nil and day - raid.start_day >= leave.max_days then return "time" end
    return nil
end

-- A marching lord army has arrived when `share` of its living raiders stand within `radius` of the lord anchor (the manor), or when
-- it marched `max_days` game days (a stuck army). The raid then starts: its start day is today. Returns true on the day of arrival.
function M.check_arrival(raid, arrival, day)
    if not raid.marching then return false end
    if raid.state ~= "active" then raid.marching = false return false end -- the army died on the way
    local near = 0
    for _, unit in pairs(raid.units) do
        if unit.x ~= nil and unit.y ~= nil and (unit.x - raid.lord.anchor.x) ^ 2 + (unit.y - raid.lord.anchor.y) ^ 2 <= arrival.radius ^ 2 then near = near + 1 end
    end
    local arrived = raid.living > 0 and near >= math.max(1, math.ceil(raid.living * arrival.share))
    if not arrived and not (day ~= nil and day - raid.spawn_day >= arrival.max_days) then return false end
    raid.marching, raid.arrival_day = false, day
    if day ~= nil then raid.start_day = day end
    -- The raid starts at arrival: the loss share and the loot goal count from the army that arrived, not from the army that left the edge.
    raid.deaths_on_march, raid.initial, raid.deaths = raid.deaths, raid.living, 0
    return true
end

-- The raid must leave. A lord army is removed by the game after peace.
function M.begin_leave(raid, reason, day)
    raid.leaving, raid.leave_reason, raid.leave_day = true, reason, day
    if raid.lord == nil then return end
    -- A lord army is removed by the game after peace. Its units that vanish are departures, not deaths.
    for _, unit in pairs(raid.units) do
        raid.carried_out = raid.carried_out + unit.loot
        unit.loot, unit.exiting = 0, true
    end
end

-- Goods the plunder tick takes today: `per_unit_day` for each living raider that stands within `battle_radius` of the anchor
-- (the player manor). Once a day. At most what is missing to the loot goal of the leave rule. A lord raid only.
function M.plunder_amount(raid, seen, plunder, leave, day, carry_cap)
    if raid.marching or raid.lord == nil or M.is_subjugation(raid) or raid.state ~= "active" or raid.leave_reason ~= nil or day == nil or raid.last_plunder_day == day then return 0 end
    raid.last_plunder_day = day
    local inside = 0
    for key in pairs(raid.units) do
        local now = seen[key]
        if now ~= nil and not now.dead and now.x ~= nil and now.y ~= nil
            and (now.x - raid.lord.anchor.x) ^ 2 + (now.y - raid.lord.anchor.y) ^ 2 <= plunder.battle_radius ^ 2 then
            inside = inside + 1
        end
    end
    local missing = math.ceil(M.loot_goal(raid, leave, carry_cap) * raid.initial) - M.looted_total(raid)
    return math.max(0, math.min(math.floor(inside * plunder.per_unit_day), missing))
end

-- `by_good` (optional) maps a good type to the amount taken. Only a Hussite raid keeps the goods (the pit give-back).
function M.record_plunder(raid, amount, by_good)
    raid.plundered = raid.plundered + amount
    if raid.lord == nil or by_good == nil then return end
    for good, count in pairs(by_good) do raid.plunder_goods[good] = (raid.plunder_goods[good] or 0) + count end
end

-- Count the dead raiders of a Hussite raid that no pit delivery has paid yet. `deaths` is the list that M.update returned.
function M.note_deaths(raid, deaths)
    if raid.lord == nil then return end
    raid.unpaid = raid.unpaid + #deaths
end

-- Share of each good for one body: floor(record / raiders at the start). The remainder is lost (owner decision 2026-10-22).
function M.body_share(raid)
    local share = {}
    if raid.lord == nil or raid.initial < 1 then return share end
    for good, count in pairs(raid.plunder_goods) do
        local part = math.floor(count / raid.initial)
        if part > 0 then share[good] = part end
    end
    return share
end

-- A pit received `bodies` new bodies. Pay one share for each unpaid dead Hussite raider, oldest raid first; extra bodies
-- (villagers, native raiders) are ignored. `raid_list` is in start order. Returns the goods to add (good -> amount) and the bodies paid.
function M.pay_bodies(raid_list, bodies)
    local goods, paid = {}, 0
    for _, raid in ipairs(raid_list) do
        while paid < bodies and raid.unpaid > 0 do
            raid.unpaid = raid.unpaid - 1
            paid = paid + 1
            for good, part in pairs(M.body_share(raid)) do goods[good] = (goods[good] or 0) + part end
        end
    end
    return goods, paid
end

function M.unpaid_total(raid_list)
    local total = 0
    for _, raid in ipairs(raid_list) do total = total + raid.unpaid end
    return total
end

-- The tier of a store type (1 or 2), or nil for a type that has no tier. `tiers` maps an EBuildingType to a tier.
function M.tier_of(tiers, building_type)
    if building_type == nil then return nil end
    return tiers[building_type]
end

-- The most goods a raid may steal in all (the steal goal), or nil when the raid does not steal. Only a baron (lord) raid of a kind in `steal.goals`.
function M.steal_goal(raid, steal)
    if raid.lord == nil then return nil end
    return steal.goals[raid.lord.kind or "plunder"]
end

-- Goods the baron steal takes today: `steal.rate` for each living raider that stands farther than `steal.threshold` from the
-- battle marker (the lord anchor). Once a day, at most what is missing to the steal goal. The game steers a game raid, so it has no steal.
function M.steal_amount(raid, seen, steal, day)
    local goal = M.steal_goal(raid, steal)
    if goal == nil or raid.marching or raid.state ~= "active" or day == nil or raid.last_steal_day == day then return 0 end
    raid.last_steal_day = day
    local far = 0
    for key in pairs(raid.units) do
        local now = seen[key]
        if now ~= nil and not now.dead and now.x ~= nil and now.y ~= nil
            and (now.x - raid.lord.anchor.x) ^ 2 + (now.y - raid.lord.anchor.y) ^ 2 > steal.threshold ^ 2 then
            far = far + 1
        end
    end
    return math.max(0, math.min(math.floor(far * steal.rate), goal - raid.stolen))
end

function M.record_steal(raid, amount) raid.stolen = raid.stolen + amount end

-- The native AI wrote its leave line: the raid is over for the village, also while the raiders still walk to the map edge.
function M.mark_leaving(raid, day)
    raid.leaving = true
    if raid.state == "active" then raid.state, raid.end_day = "left", day end
end

-- The numbers that the command and the log show.
function M.summary(raid)
    return {
        id = raid.id, start_day = raid.start_day, end_day = raid.end_day, squads = raid.squads, state = raid.state,
        initial = raid.initial, living = raid.living, deaths = raid.deaths, departures = raid.departures,
        loot = M.total_loot(raid), looted_total = M.looted_total(raid), carried_out = raid.carried_out, peak_loot = raid.peak_loot, returned = raid.returned, lost = raid.lost,
        capped = raid.capped, carry_cap = raid.carry_cap, raid_type = M.raid_type(raid), burned = raid.burned, leaving = raid.leaving, roles = raid.roles, plundered = raid.plundered, unpaid = raid.unpaid, stolen = raid.stolen, lord_raid = raid.lord ~= nil, marching = raid.marching, deaths_on_march = raid.deaths_on_march or 0, spawn_day = raid.spawn_day, arrival_day = raid.arrival_day, final = raid.lord ~= nil and raid.lord.final == true, leave_reason = raid.leave_reason, target = raid.target, kind = (raid.lord and raid.lord.kind) or "plunder",
    }
end

return M
