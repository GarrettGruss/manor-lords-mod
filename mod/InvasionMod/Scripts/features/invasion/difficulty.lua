-- Pure rules of the raid levels (no game calls). All scaling rounds up (decision 28).
-- A level is 0 (off), 1 (easy), 2 (medium) or 3 (hard). Each raid type has its own level (change update-raid-difficulty-levels, #404).
local M = {}

M.MIN, M.MAX = 1, 3
M.KINDS = { "yearly", "great", "vassal" }

-- A level of a raid type: 0 to 3.
function M.valid_level(value)
    return type(value) == "number" and value >= 0 and value <= M.MAX and value == math.floor(value)
end

-- A difficulty number for the tables (roles, scaling): 1 to 3.
function M.valid(value)
    return type(value) == "number" and value >= M.MIN and value <= M.MAX and value == math.floor(value)
end

function M.valid_kind(kind)
    for _, name in ipairs(M.KINDS) do
        if name == kind then return true end
    end
    return false
end

-- The one number for the features that are not tied to one raid type (bandits, sack, terms, fallback): the highest level, at least 1.
function M.general(levels)
    local top = M.MIN
    for _, kind in ipairs(M.KINDS) do top = math.max(top, levels[kind]) end
    return top
end

-- Ceiling of base x difficulty / max: a share that grows with difficulty.
function M.scale_up(base, difficulty)
    return math.ceil(base * difficulty / M.MAX)
end

-- Relief army squads (decisions 26 and 28): `full` at level 1, 0 at the highest, linear between, rounded up. 0 at level 0 (no great raid).
function M.relief_squads(level, full)
    if level < M.MIN then return 0 end
    return math.ceil(full * (M.MAX - level) / (M.MAX - M.MIN))
end

-- The great raid has one wave for each level point (decision 12).
function M.wave_count(level)
    return level
end

return M
