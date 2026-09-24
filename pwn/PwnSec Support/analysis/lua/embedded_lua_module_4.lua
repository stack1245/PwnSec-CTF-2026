local types = require("sql.types")
local M = {}
local Table = {}
Table.__index = Table
function Table:new(name)
    local obj = {
        name = name,
        columns = {},
        rows = {},
        column_map = {},
        primary_key = nil,
        row_count = 0,
    }
    setmetatable(obj, self)
    return obj
end
function Table:add_column(name, type_name, not_null, default_value, primary_key, unique)
    local col = {
        name = name,
        type = type_name or "TEXT",
        affinity = types.affinity_from_type(type_name),
        not_null = not_null or false,
        default_value = default_value,
        primary_key = primary_key or false,
        unique = unique or false,
    }
    table.insert(self.columns, col)
    self.column_map[name] = #self.columns
    if primary_key then
        self.primary_key = name
    end
end
function Table:add_row(row_data)
    local row = {}
    for i, col in ipairs(self.columns) do
        local value = row_data[col.name]
        if value == nil then
            value = col.default_value
        end
        if value ~= nil then
            value = types.apply_affinity(value, col.affinity)
        end
        if col.not_null and value == nil then
            error("NOT NULL constraint failed: " .. self.name .. "." .. col.name)
        end
        row[i] = value
    end
    table.insert(self.rows, row)
    self.row_count = self.row_count + 1
    return row
end
function Table:find_by_primary_key(key)
    if not self.primary_key then return nil end
    local idx = self.column_map[self.primary_key]
    if not idx then return nil end
    for i, row in ipairs(self.rows) do
        if types.equals(row[idx], key) then
            return row
        end
    end
    return nil
end
function Table:get_column_index(name)
    return self.column_map[name]
end
function Table:get_column_def(index)
    return self.columns[index]
end
function Table:row_to_dict(row)
    local dict = {}
    for i, col in ipairs(self.columns) do
        dict[col.name] = row[i]
    end
    return dict
end
function Table:delete_row(index)
    table.remove(self.rows, index)
    self.row_count = self.row_count - 1
end
function Table:update_row(index, row)
    self.rows[index] = row
end
local StorageManager = {}
StorageManager.__index = StorageManager
function StorageManager:new()
    local obj = {
        tables = {},
        table_names = {},
    }
    setmetatable(obj, self)
    return obj
end
function StorageManager:create_table(name, columns)
    if self.tables[name] then
        error("table " .. name .. " already exists")
    end
    local tbl = Table:new(name)
    for _, col_def in ipairs(columns) do
        tbl:add_column(
            col_def.name,
            col_def.type,
            col_def.not_null,
            col_def.default_value,
            col_def.primary_key,
            col_def.unique
        )
    end
    self.tables[name] = tbl
    table.insert(self.table_names, name)
    return tbl
end
function StorageManager:drop_table(name)
    if not self.tables[name] then
        error("no such table: " .. name)
    end
    self.tables[name] = nil
    for i, n in ipairs(self.table_names) do
        if n == name then
            table.remove(self.table_names, i)
            break
        end
    end
end
function StorageManager:get_table(name)
    return self.tables[name]
end
function StorageManager:has_table(name)
    return self.tables[name] ~= nil
end
function StorageManager:list_tables()
    local result = {}
    for _, name in ipairs(self.table_names) do
        table.insert(result, name)
    end
    return result
end
function StorageManager:insert(table_name, row_data)
    local tbl = self.tables[table_name]
    if not tbl then
        error("no such table: " .. table_name)
    end
    return tbl:add_row(row_data)
end
function StorageManager:select_all(table_name)
    local tbl = self.tables[table_name]
    if not tbl then
        error("no such table: " .. table_name)
    end
    local results = {}
    for _, row in ipairs(tbl.rows) do
        table.insert(results, tbl:row_to_dict(row))
    end
    return results
end
return StorageManager
