-- HarnessLoot: a stand-in for loot on the ground (spec 10, spike R3).
-- Why: the base game has no ground loot. A unit that dies loses ItemsLooted and nothing appears (spike S5, spike R3).
-- The Invasion Mode mod will define piles. This module shows that the harness can observe and drive such a mod:
--   a looter dies at a place        -> a pile is recorded at that place, with the loot of the unit
--   a peasant recovers the pile     -> the goods go back into the stock of the village
-- The piles are plain Lua tables. The recovery is instant: no peasant walks. The goods are added by the cheat manager.
-- Rules: no eval, no save function. Call only on the game thread.

local units = require("HarnessUnits")

local M = {}

M.MAX_PILES = 50
M.MAX_GOOD_TYPE = 1000
M.SIDES = { player = true, ai = true, bandit = true, civil = true }

local piles = {}      -- id -> { id, x, y, amount, good }
local nextId = 1

local function isValid(object)
    if object == nil then return false end
    local ok, valid = pcall(function() return object:IsValid() end)
    return ok and valid == true
end

local function read(fn)
    local ok, value = pcall(fn)
    if ok then return value end
    return nil
end

local function sortedPiles()
    local out = {}
    for _, pile in pairs(piles) do out[#out + 1] = pile end
    table.sort(out, function(a, b) return a.id < b.id end)
    return out
end

function M.reset()
    piles = {}
    nextId = 1
end

-- Kill up to `count` units of one side that carry loot. Each death leaves a pile at the place of the unit.
-- request.good is the good type that the pile holds (one unit of ItemsLooted is one unit of that good).
function M.drop_loot(request)
    local side = request.side or "bandit"
    local count = request.count or 1
    if not M.SIDES[side] then return { ok = false, error = "side must be player, ai, bandit or civil" } end
    if count < 1 or count > M.MAX_PILES then return { ok = false, error = "count must be 1 to " .. M.MAX_PILES } end
    if not request.good or request.good < 1 or request.good > M.MAX_GOOD_TYPE then
        return { ok = false, error = "good must be a good type from 1 to " .. M.MAX_GOOD_TYPE }
    end
    local victims = units.unitsOfSide(side, count, true)
    local made = {}
    for _, unit in ipairs(victims) do
        local amount = read(function() return unit.ItemsLooted end) or 0
        local at = read(function() return unit.realPos end)
        if #sortedPiles() >= M.MAX_PILES then return { ok = false, error = "too many piles (limit " .. M.MAX_PILES .. ")" } end
        local pile = { id = nextId, amount = amount, good = request.good,
                       x = at and math.floor(read(function() return at.X end) or 0),
                       y = at and math.floor(read(function() return at.Y end) or 0) }
        local died = pcall(function() unit:just_die() end)
        if died then
            piles[pile.id] = pile
            nextId = nextId + 1
            made[#made + 1] = pile
        end
    end
    return { ok = true, killed = #made, piles = made }
end

function M.loot_piles()
    return { ok = true, piles = sortedPiles() }
end

-- A peasant brings the pile home: the goods are added to the stock and the pile is gone.
function M.recover_loot(request)
    local pile = piles[request.pile]
    if not pile then return { ok = false, error = "no pile with id " .. tostring(request.pile) } end
    local cheat = FindFirstOf("MLCheatManager")
    if not isValid(cheat) then return { ok = false, error = "no MLCheatManager (the mod CheatManagerEnablerMod must be on)" } end
    local ok, err = pcall(function() cheat:GiveItemByID(pile.good, pile.amount) end)
    if not ok then return { ok = false, error = "GiveItemByID: " .. tostring(err) } end
    piles[pile.id] = nil
    return { ok = true, recovered = pile }
end

return M
