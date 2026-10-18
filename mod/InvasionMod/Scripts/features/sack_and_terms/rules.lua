-- Pure rules of the sack (no game calls), so a test can run them without a game.
local M = {}

-- Scaled counts and shares round up (M00 decision 28). The small epsilon stops 7.000000000000001 from becoming 8.
function M.ceil_share(total, percent)
    return math.ceil(total * percent / 100 - 1e-9)
end

-- Sack share in percent: linear in the difficulty (decision 15). `cfg` has share_min and share_max.
function M.share_percent(difficulty, cfg)
    local steps = math.max(0, math.min(2, difficulty - 1))
    return cfg.share_min + (cfg.share_max - cfg.share_min) * steps / 2
end

-- A lost battle (TBD rule): a role raid that begins to leave because it took its loot or stayed to the time limit.
-- `summary` is the raid summary of raid_behavior. A raid that was beaten (reason "losses") or paid off ("terms") is not a lost battle.
function M.is_lost_battle(summary, cfg)
    if summary == nil or not summary.roles then return false end
    for _, reason in ipairs(cfg.lost_reasons) do
        if summary.leave_reason == reason then return true end
    end
    return false
end

-- What one sack takes from a village. `census` is the HarnessSack census.
-- A fatal sack takes every family. A normal sack keeps `min_families_left` families (spike S8: no people, no game).
function M.plan(census, difficulty, cfg, fatal)
    local percent = M.share_percent(difficulty, cfg)
    local families = census.people.families or 0
    local take_families = M.ceil_share(families, percent)
    if fatal then
        take_families = families
    else
        take_families = math.max(0, math.min(take_families, families - cfg.min_families_left))
    end
    local goods = {}
    for good, held in pairs(census.stock.by_good) do
        local amount = M.ceil_share(held, percent)
        if amount > 0 then goods[good] = amount end
    end
    return { percent = percent, buildings = M.ceil_share(census.buildings.standing, percent), families = take_families, goods = goods }
end

-- The window counter. Returns the new window start and count, and whether this sack is fatal.
-- A sack outside the window starts a new window. The sack that brings the count to `limit` is fatal.
function M.count_sack(window_start, window_count, day, cfg)
    if window_count <= 0 or day - window_start >= cfg.window_days then
        window_start, window_count = day, 0
    end
    window_count = window_count + 1
    return window_start, window_count, window_count >= cfg.limit
end

-- The region to sack: the region under attack when the player owns it, else the home region when the player owns it, else nil.
-- nil means "the first region of the player" (the old behaviour). Why not always the first: after a fallback capital move (M06.03)
-- the first region can be the capital and not the village that was attacked.
function M.sack_region(target, home, player_regions)
    local owned = {}
    for _, name in ipairs(player_regions) do owned[name] = true end
    if target ~= nil and owned[target] then return target end
    if home ~= nil and owned[home] then return home end
    return nil
end

return M
