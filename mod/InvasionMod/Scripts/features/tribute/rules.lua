-- Pure rules of the tribute feature (M08). No game access.
local M = {}

-- Units of one good for one vassal: base x factor, rounded. The factor is the policy factor times the tech factor.
function M.amount(base, factor)
    return math.floor(base * factor + 0.5)
end

-- The good of an ore decal material: the exact name, else the longest known name that the material name starts with
-- (a material instance may add a suffix). Nil for other materials (game uses deerDecal_Mat).
function M.deposit_good(material, deposit_goods)
    if deposit_goods[material] then return deposit_goods[material] end
    local best
    for key, good in pairs(deposit_goods) do
        if material:sub(1, #key) == key and (best == nil or #key > #best.key) then best = { key = key, good = good } end
    end
    return best and best.good
end

-- The good names that one resource node makes rich, as a list.
-- `node` = { material = decal material name or nil, decal_x = number or nil, clumps = { { class = "Resource_Berries_C", capacity = n }, ... } }
function M.node_goods(node, rich)
    local found = {}
    local deposit = node.material and M.deposit_good(node.material, rich.deposit_goods)
    if deposit and (node.decal_x or 0) >= rich.decal_size then found[#found + 1] = deposit end
    local sums = {}
    for _, clump in ipairs(node.clumps or {}) do
        local good = rich.clump_goods[clump.class]
        if good then sums[good] = (sums[good] or 0) + (clump.capacity or 0) end
    end
    local names = {}
    for good in pairs(sums) do names[#names + 1] = good end
    table.sort(names)
    for _, good in ipairs(names) do
        local limit = rich.clump_capacity[good]
        if limit and sums[good] >= limit then found[#found + 1] = good end
    end
    return found
end

-- The goods a region pays: the detected rich goods (a set: name -> true) cut to `per_region` by priority
-- (tiers first, list order inside a tier), then filled with the fill good (flax, the stand-in for rich soil).
-- Returns the list of paid good names and the list of dropped names.
function M.choose_goods(detected, rich)
    local chosen, dropped = {}, {}
    for _, tier in ipairs(rich.priority) do
        for _, good in ipairs(tier) do
            if detected[good] then
                if #chosen < rich.per_region then chosen[#chosen + 1] = good else dropped[#dropped + 1] = good end
            end
        end
    end
    while #chosen < rich.per_region do chosen[#chosen + 1] = rich.fill_good end
    return chosen, dropped
end

-- A tick runs when the month differs from the saved one. A saved -1 means "not known yet": no tick.
function M.month_changed(current, last)
    return last >= 0 and current ~= last
end

-- A subjugation raid on a vassal region takes the vassal when it has been active for `siege_days` game days
-- and keeps at least `min_living` (a share) of its units. Returns "taken", "failed" (too few units left) or nil (still going).
function M.siege_result(summary, today, siege)
    if summary.kind ~= "subjugation" or summary.state ~= "active" or today == nil then return nil end
    if summary.initial < 1 or summary.living / summary.initial < siege.min_living then return "failed" end
    if today - summary.start_day >= siege.days then return "taken" end
    return nil
end

return M
