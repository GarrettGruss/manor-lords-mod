-- Pure rules of the scenario settings menu (change add-scenario-settings-menu, #375). No game calls, so a test can run them.
local M = {}

-- The five settings, in the order of the rows. `values` are the numbers stored in the mod state, in the order of the choices.
M.ROWS = {
    { key = "yearly", values = { 0, 1, 2, 3 } },   -- the three levels: 0 off, 1 easy, 2 medium, 3 hard
    { key = "great", values = { 0, 1, 2, 3 } },
    { key = "vassal", values = { 0, 1, 2, 3 } },
    { key = "first_raid_years", values = { 1, 2, 3 } },
    { key = "size_class", values = { 1, 2, 3 } },
}

local function row_of(key)
    for index, row in ipairs(M.ROWS) do
        if row.key == key then return row, index end
    end
    return nil
end

local function index_of(row, value)
    for index, candidate in ipairs(row.values) do
        if candidate == value then return index end
    end
    return nil
end

function M.is_valid_value(key, value)
    local row = row_of(key)
    return row ~= nil and type(value) == "number" and index_of(row, value) ~= nil
end

function M.defaults(config)
    local copy = {}
    for _, row in ipairs(M.ROWS) do copy[row.key] = config.defaults[row.key] end
    return copy
end

-- Returns a copy of `selection` with `key` set to `value`, or nil and a message.
function M.choose(selection, key, value)
    if not M.is_valid_value(key, value) then
        return nil, string.format("setting %s: %s is not a valid choice", tostring(key), tostring(value))
    end
    local copy = {}
    for name, current in pairs(selection) do copy[name] = current end
    copy[key] = value
    return copy
end

-- A click on the menu. `action` is "choose" (row key and value), "defaults" or "begin".
-- Returns the new selection and whether the player wants to begin the game, or nil and a message.
function M.click(selection, config, action, key, value)
    if action == "defaults" then return M.defaults(config), false end
    if action == "begin" then return selection, true end
    if action == "choose" then
        local chosen, problem = M.choose(selection, key, value)
        if not chosen then return nil, problem end
        return chosen, false
    end
    return nil, "unknown action " .. tostring(action)
end

-- The text of one choice button. The chosen one is marked, so a screenshot and the test show it.
function M.choice_text(config, key, index, selected)
    local name = config.choice_names[key][index]
    if selected then return "> " .. name .. " <" end
    return name
end

-- Which choice of a row is selected: the index (1 to 4), or nil.
function M.selected_index(selection, key)
    local row = row_of(key)
    return row and index_of(row, selection[key]) or nil
end

-- New game or loaded game (spec "A new game is told from a loaded save").
-- `info` = { save_file = string or nil (nil: not readable), applied = 0 or 1, day = number or nil }.
-- Returns "loaded" (the mod state holds the settings), "old_save" (a save without settings: defaults, no menu),
-- "new" (open the menu) or "unknown" (the inputs are not readable yet: do nothing, ask again later).
function M.kind_of_game(info, config)
    if info.applied == 1 then return "loaded" end
    if info.save_file == nil then return "unknown" end
    if info.save_file ~= "" then return "old_save" end
    -- No save file name. The game may have lost it after a load (the load bug of 2026-10-11), so the day decides too.
    if info.day ~= nil and info.day > config.new_game_max_day then return "old_save" end
    return "new"
end

-- Was the game started from the template "The Hussites Are Coming" (change add-hussite-scenario-template, #451)?
-- The game keeps no template name, so the marker is the settings combination of the template row. No game template has
-- Royal tax None together with Difficult weather and Low approval penalty.
-- `setup` = { royal_tax, weather, approval_loss, ai_lords, adversary_baron, max_bandit_camps, initial_bandit_camps }. A missing value gives false.
function M.is_hussite_template(setup)
    if type(setup) ~= "table" then return false end
    return setup.royal_tax == 0 and setup.weather == 2 and setup.approval_loss == 0.5
        and setup.ai_lords == 0 and setup.adversary_baron == false
        and setup.max_bandit_camps == 0 and setup.initial_bandit_camps == 0
end

-- The guard value `vassals` (change add-game-settings-guard, #438): 1 vassals work, 0 they do not, -1 not known yet.
-- AI opponents (numGenericAILords) 0 means no AI lord, so no vassals. A count that cannot be read gives nil (not known).
function M.vassals_from_setup(setup)
    if type(setup) ~= "table" or type(setup.ai_lords) ~= "number" then return nil end
    return setup.ai_lords > 0 and 1 or 0
end

-- The live check of a save without the value: no AI lord pawn means no vassals. A count that cannot be read gives nil.
function M.vassals_from_lord_count(count)
    if type(count) ~= "number" then return nil end
    return count > 0 and 1 or 0
end

-- The text of the background block. A warning is added below the background when vassals are not enabled.
function M.background_with_warning(config, vassals)
    if vassals ~= 0 then return config.background_text end
    return config.background_text .. "\n\n" .. config.vassals_warning
end

-- The start kit is given once, in a new game only (a loaded save never gets it).
function M.kit_due(is_new_game, given)
    return is_new_game == true and given ~= 1
end

-- How many people must go so that the village has `target` people. A village with fewer people loses none.
function M.people_to_remove(population, target)
    return math.max(0, population - target)
end

return M
