-- OrderProbe: harness-only probe mod for spike-public-order-factor (#403), route A. Not shipped.
-- hold(target) writes Region.publicOrder = target on every loop tick. Before each write it reads the value, so the
-- reads show how often the game value comes back (flicker). hold(-1) only reads (control run).
local commands = require("HarnessCommands")
local core = require("ManorCore")
local log = require("HarnessLog")

local P = "OrderProbe."
local state = { running = false, target = -1, ticks = 0, own = 0, other = 0, others = {}, writes = 0, write_errors = 0, days = {}, last_other = nil }

local function engine() local e = FindFirstOf("RTSMultiEngineCPP"); if e ~= nil and e:IsValid() then return e end end

local function day()
    local e = engine()
    if not e then return nil end
    local ok, v = pcall(function() return e.TemporalComponent.daysTotal end)
    if ok and type(v) == "number" then return math.floor(v) end
end

local function tick()
    local region = core.player_region()
    if not region then return end
    local ok, order, approval = pcall(function() return region.publicOrder, region.Approval end)
    if not ok then return end
    local d = day() or -1
    local row = state.days[d]
    if not row then row = { n = 0, own = 0, other = 0, min_ap = approval, max_ap = approval, vals = {} }; state.days[d] = row end
    row.n = row.n + 1
    row.min_ap = math.min(row.min_ap, approval); row.max_ap = math.max(row.max_ap, approval)
    state.ticks = state.ticks + 1
    if state.target >= 0 and order == state.target then
        state.own = state.own + 1; row.own = row.own + 1
    else
        state.other = state.other + 1; row.other = row.other + 1
        state.others[order] = (state.others[order] or 0) + 1
        row.vals[order] = (row.vals[order] or 0) + 1
    end
    row.last_order = order; row.last_ap = approval
    local okf, fam = pcall(function() return region:getTotalNumFamilies() end)
    if okf then row.families = fam end
    if state.target >= 0 then
        local w, problem = pcall(function() region.publicOrder = state.target end)
        if w then state.writes = state.writes + 1 else state.write_errors = state.write_errors + 1 end
    end
end

local function loop()
    LoopAsync(100, function()
        if not state.running then return true end
        ExecuteInGameThread(function() local ok, e = pcall(tick); if not ok then log.say("OrderProbe", tostring(e)) end end)
        return false
    end)
end

commands.register(P .. "hold", function(a)
    state = { running = true, target = a.target, ticks = 0, own = 0, other = 0, others = {}, writes = 0, write_errors = 0, days = {} }
    loop()
    return { ok = true, target = a.target }
end, { target = { type = "integer", required = true, min = -1, max = 100 } })
commands.register(P .. "stop", function() state.running = false; return { ok = true } end)
commands.register(P .. "stats", function()
    local days = {}
    for d, row in pairs(state.days) do
        days[#days + 1] = { day = d, n = row.n, own = row.own, other = row.other, last_order = row.last_order, last_ap = row.last_ap, min_ap = row.min_ap, max_ap = row.max_ap, families = row.families, vals = row.vals }
    end
    table.sort(days, function(x, y) return x.day < y.day end)
    return { ticks = state.ticks, own = state.own, other = state.other, others = state.others, writes = state.writes, write_errors = state.write_errors, days = days }
end)
commands.register(P .. "now", function()
    local region = core.player_region()
    if not region then return { ok = false } end
    return { order = region.publicOrder, approval = region.Approval, families = region:getTotalNumFamilies(), day = day() }
end)
log.say("OrderProbe", "loaded")
