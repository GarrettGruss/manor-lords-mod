-- Pure rules of the feature liege_influence. No game access.
local M = {}

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
