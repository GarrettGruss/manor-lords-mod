-- HarnessDataTable: read, and change, single number fields of rows in one DataTable (spec 09, first check).
-- Why: the bridge cannot read a DataTable safely. Reading `RowStruct` or the `Item` struct through the bridge
-- ended the game, because the bridge reads every field of a struct and one field is a SoftClass (see datatable-check.md).
-- This module reads only the fields that are listed in FIELDS. Each one is a plain float of the `Item` struct.
-- Only one table is allowed: RTSMultiEngineCPP.itemStats (DT_Items).

local M = {}

M.TABLE_PROPERTY = "itemStats"
-- Offsets are from the jmap: Weight 124, Value 224, spoilageRate 232 (all FloatProperty of /Script/ManorLords.Item).
M.FIELDS = { Weight = true, Value = true, spoilageRate = true }
local MAX_NAMES = 12

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

-- Return the table object, or nil and a reason.
local function findTable()
    local engine = FindFirstOf("RTSMultiEngineCPP")
    if not isValid(engine) then return nil, "no RTSMultiEngineCPP" end
    local ok, table_ = pcall(function() return engine[M.TABLE_PROPERTY] end)
    if not ok or not isValid(table_) then return nil, "no valid " .. M.TABLE_PROPERTY .. " table" end
    return table_
end

function M.check_field(field)
    if M.FIELDS[field] ~= true then return false, "field not allowed: " .. tostring(field) end
    return true
end

-- Row count, a sample of row names and the row struct name. Each part is read on its own, so one failure shows.
function M.info()
    local table_, problem = findTable()
    if not table_ then return nil, problem end
    local out = { table = textOf(table_:GetFullName()) }
    local okCount, count = pcall(function() return #table_ end)
    if okCount then out.row_count = count else out.row_count_error = tostring(count) end
    local okNames, names = pcall(function() return table_:GetRowNames() end)
    if okNames then
        out.names = {}
        for i = 1, math.min(#names, MAX_NAMES) do out.names[i] = textOf(names[i]) end
    else
        out.names_error = tostring(names)
    end
    local okStruct, struct = pcall(function() return table_:GetRowStruct():GetFullName() end)
    if okStruct then out.row_struct = textOf(struct) else out.row_struct_error = tostring(struct) end
    return out
end

local function findRow(rowName)
    local table_, problem = findTable()
    if not table_ then return nil, problem end
    local ok, row = pcall(function() return table_:FindRow(rowName) end)
    if not ok then return nil, "FindRow failed: " .. tostring(row) end
    if row == nil then return nil, "no row named " .. tostring(rowName) end
    return row
end

-- Read the listed fields of one row. Only fields in FIELDS are read.
function M.read_row(rowName, fields)
    local row, problem = findRow(rowName)
    if not row then return nil, problem end
    local out = {}
    for _, field in ipairs(fields) do
        local allowed, why = M.check_field(field)
        if not allowed then return nil, why end
        local ok, value = pcall(function() return row[field] end)
        if not ok then return nil, "reading " .. field .. " failed: " .. tostring(value) end
        out[field] = value
    end
    return out
end

-- Write one number field of one row and read it back.
function M.write_number(rowName, field, value)
    local allowed, why = M.check_field(field)
    if not allowed then return nil, why end
    if type(value) ~= "number" or value ~= value then return nil, "value must be a number" end
    local row, problem = findRow(rowName)
    if not row then return nil, problem end
    local before = row[field]
    local ok, err = pcall(function() row[field] = value end)
    if not ok then return nil, "writing " .. field .. " failed: " .. tostring(err) end
    local freshRow = findRow(rowName)
    return { before = before, after = freshRow and freshRow[field] or nil }
end

return M
