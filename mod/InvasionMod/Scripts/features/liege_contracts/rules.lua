-- Pure rules of the feature liege_contracts. No game access, so plain Lua and the fake game can test them.
local M = {}

---------------------------------------------------------------------------------------------
-- Saved text. ModState strings allow only letters, digits, _ . and -, so a list is "a.b.c" and a
-- number list is "o0-12.o1-40" (notes/state-encoding.md).
---------------------------------------------------------------------------------------------

function M.join_ids(ids) return table.concat(ids, ".") end

function M.split_ids(text)
    local ids = {}
    if text == nil or text == "" then return ids end
    for id in string.gmatch(text, "[^%.]+") do ids[#ids + 1] = id end
    return ids
end

-- values: { [index] = number } with 1-based indexes; the text uses 0-based indexes: "o0-12.o1-40". Extra keys (names) use their own name.
function M.encode_numbers(values, names)
    local parts = {}
    for index, value in ipairs(values) do parts[#parts + 1] = string.format("o%d-%d", index - 1, math.floor(value)) end
    for _, name in ipairs(names or {}) do
        if values[name] ~= nil then parts[#parts + 1] = string.format("%s-%d", name, math.floor(values[name])) end
    end
    return table.concat(parts, ".")
end

function M.decode_numbers(text)
    local values = {}
    if text == nil or text == "" then return values end
    for entry in string.gmatch(text, "[^%.]+") do
        local key, number = entry:match("^(%a+%d*)%-(%d+)$")
        if key ~= nil then
            local index = key:match("^o(%d+)$")
            values[index and (tonumber(index) + 1) or key] = tonumber(number)
        end
    end
    return values
end

---------------------------------------------------------------------------------------------
-- The draw
---------------------------------------------------------------------------------------------

-- Weighted draw without replacement. `rng()` returns a number in [0, 1). Returns a list of `count` ids, or nil and a message.
function M.draw(contracts, count, rng)
    if #contracts < count then return nil, string.format("only %d contracts, %d wanted", #contracts, count) end
    local pool = {}
    for _, contract in ipairs(contracts) do pool[#pool + 1] = { id = contract.id, weight = contract.weight } end
    local picked = {}
    for _ = 1, count do
        local total = 0
        for _, row in ipairs(pool) do total = total + row.weight end
        local point, chosen = rng() * total, #pool
        for index, row in ipairs(pool) do
            point = point - row.weight
            if point < 0 then chosen = index break end
        end
        picked[#picked + 1] = table.remove(pool, chosen).id
    end
    return picked
end

---------------------------------------------------------------------------------------------
-- Progress
---------------------------------------------------------------------------------------------

-- The number an objective must reach.
function M.target(objective)
    if objective.type == "hold_public_order" then return objective.days end
    return objective.amount
end

-- The progress of one objective from a reading of the world.
-- reading: { stock = { [good] = n }, buildings = { [type] = n }, kills = n, squads = n }
-- baseline: the numbers taken at the pick (build count, kills). Hold public order is updated with M.hold_step.
function M.measure(objective, reading, baseline)
    local kind = objective.type
    if kind == "deliver_goods" then return math.floor((reading.stock or {})[objective.good] or 0) end
    if kind == "build_count" then return math.max(0, math.floor(((reading.buildings or {})[objective.building_type] or 0) - (baseline or 0))) end
    if kind == "kill_raiders" then return math.max(0, math.floor((reading.kills or 0) - (baseline or 0))) end
    if kind == "raise_militia_squads" then return math.floor(reading.squads or 0) end
    return nil
end

-- Kills are a running total: the counter of `raid_behavior` restarts at 0 in a new session (a load), so the progress adds the
-- rise of the counter since the last look. `seen` is nil at the first look of a session (nothing is added). A fall of the
-- counter counts as a restart. Returns the new progress and the new `seen`.
function M.add_kills(progress, seen, now)
    if now == nil then return progress, seen end
    if seen == nil or now < seen then return progress, now end
    return progress + (now - seen), now
end

-- Hold public order. `last_day` is the last day that was counted (the start day at the pick). Days that pass count while the
-- order is at or above `min`; one look under `min` resets the streak to 0. Returns the new progress and the new last day.
function M.hold_step(progress, last_day, day, order, min)
    if day == nil or order == nil or last_day == nil or day <= last_day then return progress, last_day end
    if order >= min then return progress + (day - last_day), day end
    return 0, day
end

function M.is_complete(objectives, progress)
    for index, objective in ipairs(objectives) do
        if (progress[index] or 0) < M.target(objective) then return false end
    end
    return true
end

-- The first objective that is short: { index, missing } or nil.
function M.missing(objectives, progress)
    for index, objective in ipairs(objectives) do
        local short = M.target(objective) - (progress[index] or 0)
        if short > 0 then return { index = index, objective = objective, missing = short } end
    end
    return nil
end

---------------------------------------------------------------------------------------------
-- Deadline and penalty
---------------------------------------------------------------------------------------------

-- Is the contract due? `now`: { day, season, season_no }. `picked`: { day, season_no } at the pick.
-- A "winter_start" contract fails when winter has begun after the pick (the season counter is above the counter of the pick).
-- A numeric duration fails when that many game days have passed. Returns true, or false and nothing.
function M.is_due(duration, picked, now, winter_season)
    if duration == "winter_start" then
        if now.season == nil or now.season_no == nil or picked.season_no == nil then return false end
        return now.season == winter_season and now.season_no > picked.season_no
    end
    if now.day == nil or picked.day == nil then return false end
    return now.day - picked.day >= duration
end

-- The influence after a failed contract. Never below 0.
function M.after_penalty(influence, penalty)
    return math.max(0, (influence or 0) - penalty)
end

-- The pick is refused with a reason, or nil.
function M.pick_refusal(offer, active_id, id)
    if active_id ~= nil and active_id ~= "" then return "a contract is already active: " .. active_id end
    if #offer == 0 then return "the liege offers no contracts now" end
    for _, offered in ipairs(offer) do
        if offered == id then return nil end
    end
    return "the contract '" .. tostring(id) .. "' is not in the offer"
end

return M
