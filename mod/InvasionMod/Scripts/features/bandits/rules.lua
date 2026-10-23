-- Pure rules of the bandits feature. No game access, so the fake game and plain Lua can test them.
-- The mod keeps its own public order (mod order). Every tick adds the manor term and removes the homeless term.
-- Low order starts a timer. When the timer expires, villagers leave to become bandits.
local M = {}

function M.clamp_order(value)
    return math.max(0, math.min(100, value))
end

-- A tick is due when `tick_days` game days passed since the last tick. last < 0: no tick yet, the caller only stores the day.
function M.tick_due(today, last, tick_days)
    return last >= 0 and today - last >= tick_days
end

-- One order tick. cfg: manor_term, homeless_term. order_bonus (tech tree) is added to the manor term.
-- Returns the record the telemetry and the log use.
function M.tick_order(order, homeless_count, order_bonus, cfg)
    local manor_term = cfg.manor_term + (order_bonus or 0)
    local homeless_term = cfg.homeless_term * homeless_count
    return {
        order_before = order, manor_term = manor_term, homeless_count = homeless_count,
        homeless_term = homeless_term, order_after = M.clamp_order(order + manor_term - homeless_term),
    }
end

-- What the banditry timer does now. timer_start < 0: no timer.
-- Returns action ("none", "start", "reset", "wait", "leave"), days_left (nil without a timer) and warn (true when the 30 day warning is due).
function M.timer_step(order, timer_start, today, cfg)
    if timer_start < 0 then
        if order < cfg.threshold then return { action = "start", days_left = cfg.timer_days } end
        return { action = "none" }
    end
    if order >= cfg.threshold then return { action = "reset" } end
    local left = cfg.timer_days - (today - timer_start)
    if left <= 0 then return { action = "leave", days_left = 0 } end
    return { action = "wait", days_left = left, warn = left <= cfg.warn_days }
end

-- Families that leave: at most `leavers`, and the village keeps `min_left`.
function M.leavers_for(families, cfg)
    return math.max(0, math.min(cfg.leavers, families - cfg.min_families_left))
end

-- Order after the leave.
function M.order_after_leave(order, cfg)
    return M.clamp_order(order + cfg.order_gain)
end

-- Buy-back (iteration 03). Scaled values round up (M00 decision 30).
function M.buy_back_price(families, cfg)
    return math.ceil(families * cfg.silver_per_family * cfg.price_multiplier)
end

function M.families_to_return(outstanding, free_slots)
    return math.max(0, math.min(outstanding, free_slots))
end

-- Returns nil when the buy-back may go on, or the reason for the refusal.
-- facts: outstanding (families), bandit_units, free_slots, silver. cfg: the buy_back config table.
function M.buy_back_refusal(facts, cfg)
    if facts.outstanding < 1 then return "no families to bring back" end
    if facts.bandit_units < 1 then return "no bandit units on the map" end
    if facts.free_slots < 1 then return "no free home slot" end
    local price = M.buy_back_price(M.families_to_return(facts.outstanding, facts.free_slots), cfg)
    if facts.silver < price then return string.format("silver %d is below the price %d", facts.silver, price) end
    return nil
end

-- The game takes the silver when it removes the bandits, but it brings back families only some of the time (spike S1: 12 of 15).
-- When no family came back, the mod gives back what the game took, at most the price.
function M.refund_amount(silver_before, silver_now, price)
    return math.max(0, math.min(price, silver_before - silver_now))
end

return M
