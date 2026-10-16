-- Pure logic that orders and loads features. It does not use any game API, so a fake-game test can run it.

local M = {}

-- The names of the enabled features, each one after the features it requires.
-- Fails with a clear message on a duplicate, a missing feature, a disabled requirement or a cycle.
function M.order(features, config)
    local by_name = {}
    for _, feature in ipairs(features) do
        if by_name[feature.name] then error("feature list: duplicate feature '" .. feature.name .. "'", 0) end
        by_name[feature.name] = feature
    end
    for name in pairs(config) do
        if not by_name[name] then error("config: unknown feature '" .. name .. "' (not in the feature list)", 0) end
    end

    local function is_enabled(name)
        local entry = config[name]
        return entry ~= nil and entry.enabled == true
    end

    local ordered, state = {}, {}
    local function visit(name, path)
        if state[name] == "done" then return end
        if state[name] == "visiting" then
            error("feature cycle: " .. table.concat(path, " -> ") .. " -> " .. name, 0)
        end
        state[name] = "visiting"
        path[#path + 1] = name
        for _, needed in ipairs(by_name[name].requires or {}) do
            if not by_name[needed] then
                error("feature '" .. name .. "' requires '" .. needed .. "', which is not in the feature list", 0)
            end
            if not is_enabled(needed) then
                error("feature '" .. name .. "' requires '" .. needed .. "', which is disabled in config.lua", 0)
            end
            visit(needed, path)
        end
        path[#path] = nil
        state[name] = "done"
        ordered[#ordered + 1] = name
    end

    for _, feature in ipairs(features) do
        if is_enabled(feature.name) then visit(feature.name, {}) end
    end
    return ordered
end

-- Load the enabled features in order. `require_feature(path)` loads a module. A failing feature stops the load.
-- A feature module lives at "features.<name>.init" (explicit, because UE4SS may not search "?/init.lua").
function M.load(features, config, require_feature, log)
    local names = M.order(features, config)
    for _, name in ipairs(names) do
        local path = "features." .. name .. ".init"
        local ok, error_text = pcall(require_feature, path)
        if not ok then error("feature '" .. name .. "' failed to load (" .. path .. "): " .. tostring(error_text), 0) end
        log("feature loaded: " .. name)
    end
    return names
end

return M
