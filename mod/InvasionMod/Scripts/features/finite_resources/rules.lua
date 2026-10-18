-- Pure rules of the finite resources feature (M10). No game access.
local M = {}

M.UNKNOWN = -1 -- a total that was not read yet

-- Units produced since the last look. A first look (last unknown) and a fall of the total (a lost building) count as 0.
function M.delta(total, last)
    if last == M.UNKNOWN or total <= last then return 0 end
    return total - last
end

function M.remaining(size, mined)
    return math.max(0, size - mined)
end

function M.is_empty(size, mined)
    return mined >= size
end

return M
