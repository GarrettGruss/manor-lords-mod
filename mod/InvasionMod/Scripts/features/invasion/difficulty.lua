-- Pure rules of the difficulty (no game calls). All scaling rounds up (decision 28).
local M = {}

M.MIN, M.MAX = 1, 3

function M.valid(value)
    return type(value) == "number" and value >= M.MIN and value <= M.MAX and value == math.floor(value)
end

-- Ceiling of base x difficulty / max: a share that grows with difficulty.
function M.scale_up(base, difficulty)
    return math.ceil(base * difficulty / M.MAX)
end

-- Relief army squads (decisions 26 and 28): `full` at difficulty 1, 0 at the highest, linear between, rounded up.
function M.relief_squads(difficulty, full)
    return math.ceil(full * (M.MAX - difficulty) / (M.MAX - M.MIN))
end

-- The great raid has one wave for each difficulty point (decision 12).
function M.wave_count(difficulty)
    return difficulty
end

return M
