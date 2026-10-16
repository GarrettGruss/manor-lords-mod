-- HarnessDataTable: read, and change, single number fields of rows in a DataTable (spec 09, first check; spec 10, spike S7).
-- Why: the bridge cannot read a DataTable safely. Reading `RowStruct` or the `Item` struct through the bridge
-- ended the game, because the bridge reads every field of a struct and one field is a SoftClass (see datatable-check.md).
-- This module reads only the fields that are listed per table. Each one is a plain number of the row struct.
-- Only two tables are allowed:
--   items: RTSMultiEngineCPP.itemStats (DT_Items), the default.
--   units: DT_UnitTemplates, found by its object path. The game has no DT_units. (spike S7)
-- A write changes the table in memory only. It never writes a file.

local M = {}

M.TABLE_PROPERTY = "itemStats"
M.DEFAULT_KIND = "items"
-- Offsets are from the jmap: Weight 124, Value 224, spoilageRate 232 (all FloatProperty of /Script/ManorLords.Item).
-- Units: /Script/ManorLords.UnitTemplate cost 100 (float), maxSize 256 (int), minMeleeTraining 296 and minArcheryTraining 300 (float),
-- minHouseLv 304 (int), combatExperience 312 (float).
M.TABLES = {
    -- def, block, att, armorPierce: combat numbers of Item (spec 25).
    items = { fields = { Weight = true, Value = true, spoilageRate = true, def = true, block = true, att = true, armorPierce = true } },
    units = {
        path = "/Game/NotStronghold/Data/DT_UnitTemplates.DT_UnitTemplates",
        fields = { cost = true, maxSize = true, minMeleeTraining = true, minArcheryTraining = true, minHouseLv = true, combatExperience = true },
    },
}
-- Kept for old callers: the field list of the default table.
M.FIELDS = M.TABLES.items.fields
local MAX_NAMES = 12
local MAX_ROWS = 300

local function isValid(object)
    if object == nil then return false end
    local ok, valid = pcall(function() return object:IsValid() end)
    return ok and valid == true
end

local function textOf(value)
    if type(value) == "string" then return value end
    local ok, text = pcall(function() return value:ToString() end)
    return ok and text or tostring(value)
end

local function tableKind(kind)
    kind = kind or M.DEFAULT_KIND
    local definition = M.TABLES[kind]
    if not definition then return nil, "unknown table: " .. tostring(kind) end
    return definition, kind
end

-- Return the table object, or nil and a reason.
local function findTable(kind)
    local definition, why = tableKind(kind)
    if not definition then return nil, why end
    if definition.path then
        local ok, found = pcall(StaticFindObject, definition.path)
        if not ok or not isValid(found) then return nil, "no valid " .. kind .. " table at " .. definition.path end
        return found
    end
    local engine = FindFirstOf("RTSMultiEngineCPP")
    if not isValid(engine) then return nil, "no RTSMultiEngineCPP" end
    local ok, table_ = pcall(function() return engine[M.TABLE_PROPERTY] end)
    if not ok or not isValid(table_) then return nil, "no valid " .. M.TABLE_PROPERTY .. " table" end
    return table_
end

function M.check_field(field, kind)
    local definition, why = tableKind(kind)
    if not definition then return false, why end
    if definition.fields[field] ~= true then return false, "field not allowed: " .. tostring(field) end
    return true
end

-- Row count, a sample of row names and the row struct name. Each part is read on its own, so one failure shows.
function M.info(kind)
    local table_, problem = findTable(kind)
    if not table_ then return nil, problem end
    local out = { table = textOf(table_:GetFullName()) }
    local okCount, count = pcall(function() return #table_ end)
    if okCount then out.row_count = count else out.row_count_error = tostring(count) end
    local okNames, names = pcall(function() return table_:GetRowNames() end)
    if okNames then
        out.names = {}
        for i = 1, math.min(#names, MAX_NAMES) do out.names[i] = textOf(names[i]) end
        out.name_count = #names
    else
        out.names_error = tostring(names)
    end
    local okStruct, struct = pcall(function() return table_:GetRowStruct():GetFullName() end)
    if okStruct then out.row_struct = textOf(struct) else out.row_struct_error = tostring(struct) end
    return out
end

local function findRow(rowName, kind)
    local table_, problem = findTable(kind)
    if not table_ then return nil, problem end
    local ok, row = pcall(function() return table_:FindRow(rowName) end)
    if not ok then return nil, "FindRow failed: " .. tostring(row) end
    if row == nil then return nil, "no row named " .. tostring(rowName) end
    return row
end

-- All row names of a table, in table order (rows whose name starts with "--" are separators and are skipped).
function M.row_names(kind)
    local table_, problem = findTable(kind)
    if not table_ then return nil, problem end
    local ok, names = pcall(function() return table_:GetRowNames() end)
    if not ok then return nil, "GetRowNames failed: " .. tostring(names) end
    local out = {}
    for i = 1, math.min(#names, MAX_ROWS) do
        local name = textOf(names[i])
        if name:sub(1, 2) ~= "--" then out[#out + 1] = name end
    end
    return out
end

function M.has_row(rowName, kind)
    local row = findRow(rowName, kind)
    return row ~= nil
end

-- Read the listed fields of one row. Only fields in the list of the table are read.
function M.read_row(rowName, fields, kind)
    local row, problem = findRow(rowName, kind)
    if not row then return nil, problem end
    local out = {}
    for _, field in ipairs(fields) do
        local allowed, why = M.check_field(field, kind)
        if not allowed then return nil, why end
        local ok, value = pcall(function() return row[field] end)
        if not ok then return nil, "reading " .. field .. " failed: " .. tostring(value) end
        out[field] = value
    end
    return out
end

local function sortedFields(kind)
    local definition = tableKind(kind)
    local names = {}
    for name in pairs(definition.fields) do names[#names + 1] = name end
    table.sort(names)
    return names
end

-- Every row with every allowed field: { {row = "name", values = {field = number}}, ... }.
function M.read_all(kind)
    local names, problem = M.row_names(kind)
    if not names then return nil, problem end
    local fields, rows = sortedFields(kind), {}
    for _, name in ipairs(names) do
        local values, why = M.read_row(name, fields, kind)
        if not values then return nil, name .. ": " .. tostring(why) end
        rows[#rows + 1] = { row = name, values = values }
    end
    return rows
end

-- Write one number field of one row and read it back.
function M.write_number(rowName, field, value, kind)
    local allowed, why = M.check_field(field, kind)
    if not allowed then return nil, why end
    if type(value) ~= "number" or value ~= value then return nil, "value must be a number" end
    local row, problem = findRow(rowName, kind)
    if not row then return nil, problem end
    local before = row[field]
    local ok, err = pcall(function() row[field] = value end)
    if not ok then return nil, "writing " .. field .. " failed: " .. tostring(err) end
    local freshRow = findRow(rowName, kind)
    return { before = before, after = freshRow and freshRow[field] or nil }
end

return M
