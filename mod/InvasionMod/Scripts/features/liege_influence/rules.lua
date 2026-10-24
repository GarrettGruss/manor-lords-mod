-- Pure rules of the feature liege_influence. No game access.
local M = {}

function M.gain(amount, influence_per_unit)
    return amount * influence_per_unit
end

-- Returns nil when the treasury can pay the amount, else the reason for the refusal.
function M.refusal(amount, silver)
    if type(amount) ~= "number" or amount < 1 or amount ~= math.floor(amount) then return "the amount must be a whole number of at least 1" end
    if silver == nil then return "the silver of the lord's treasury is not known" end
    if silver < amount then return string.format("not enough silver: %d needed, %d held", amount, silver) end
    return nil
end

-- The arms shipment button (change add-scenario-start-kit, #425).
-- `last_day` is the game day of the last shipment, or a number below 0 for none. Returns { enabled, reason, days_left }.
function M.shipment_status(cfg, silver, day, last_day)
    if type(day) ~= "number" then return { enabled = false, reason = "the game day is not known", days_left = 0 } end
    local days_left = 0
    if type(last_day) == "number" and last_day >= 0 then days_left = math.max(0, cfg.cooldown_days - (day - last_day)) end
    if days_left > 0 then
        return { enabled = false, reason = string.format("%d days left", math.ceil(days_left)), days_left = days_left }
    end
    if type(silver) ~= "number" then return { enabled = false, reason = "the silver is not known", days_left = 0 } end
    if silver < cfg.cost then
        return { enabled = false, reason = string.format("need %d silver, %d missing", cfg.cost, cfg.cost - silver), days_left = 0 }
    end
    return { enabled = true, days_left = 0 }
end

-- Total units of a goods list.
function M.goods_total(goods)
    local total = 0
    for _, good in ipairs(goods) do total = total + good.amount end
    return total
end

return M
