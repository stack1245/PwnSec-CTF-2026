local types = require("sql.types")
local storage = require("sql.storage")
local M = {}
local function eval_expression(expr, row, tables)
    if not expr then return nil end
    local etype = expr.type
    if etype == "LITERAL" then
        return expr.value
    elseif etype == "STAR" then
        return "*"
    elseif etype == "COLUMN" then
        local table_alias = expr.table
        local col_name = expr.column
        if table_alias then
            for _, t in ipairs(tables) do
                if t.alias == table_alias or t.name == table_alias then
                    local idx = t.table:get_column_index(col_name)
                    if idx then
                        return row[t.row_offset + idx]
                    end
                end
            end
        else
            for _, t in ipairs(tables) do
                local idx = t.table:get_column_index(col_name)
                if idx then
                    return row[t.row_offset + idx]
                end
            end
        end
        return nil
    elseif etype == "ADD" then
        local a = eval_expression(expr.left, row, tables)
        local b = eval_expression(expr.right, row, tables)
        if a == nil or b == nil then return nil end
        local na, nb = types.to_number(a), types.to_number(b)
        if na == nil or nb == nil then return nil end
        return na + nb
    elseif etype == "SUB" then
        local a = eval_expression(expr.left, row, tables)
        local b = eval_expression(expr.right, row, tables)
        if a == nil or b == nil then return nil end
        local na, nb = types.to_number(a), types.to_number(b)
        if na == nil or nb == nil then return nil end
        return na - nb
    elseif etype == "MUL" then
        local a = eval_expression(expr.left, row, tables)
        local b = eval_expression(expr.right, row, tables)
        if a == nil or b == nil then return nil end
        local na, nb = types.to_number(a), types.to_number(b)
        if na == nil or nb == nil then return nil end
        return na * nb
    elseif etype == "DIV" then
        local a = eval_expression(expr.left, row, tables)
        local b = eval_expression(expr.right, row, tables)
        if a == nil or b == nil then return nil end
        local na, nb = types.to_number(a), types.to_number(b)
        if na == nil or nb == nil then return nil end
        if nb == 0 then return nil end
        return na / nb
    elseif etype == "MOD" then
        local a = eval_expression(expr.left, row, tables)
        local b = eval_expression(expr.right, row, tables)
        if a == nil or b == nil then return nil end
        local na, nb = types.to_number(a), types.to_number(b)
        if na == nil or nb == nil then return nil end
        if nb == 0 then return nil end
        return na % nb
    elseif etype == "NEG" then
        local a = eval_expression(expr.expr, row, tables)
        if a == nil then return nil end
        local na = types.to_number(a)
        if na == nil then return nil end
        return -na
    elseif etype == "AND" then
        local a = eval_expression(expr.left, row, tables)
        if a == nil or a == false then return false end
        local b = eval_expression(expr.right, row, tables)
        if b == nil then return nil end
        return (a and b) ~= false
    elseif etype == "OR" then
        local a = eval_expression(expr.left, row, tables)
        local b = eval_expression(expr.right, row, tables)
        if a == nil and b == nil then return nil end
        if a == true or b == true then return true end
        if a == nil or b == nil then return nil end
        return false
    elseif etype == "NOT" then
        local a = eval_expression(expr.expr, row, tables)
        if a == nil then return nil end
        return not a
    elseif etype == "COMPARISON" then
        local a = eval_expression(expr.left, row, tables)
        local b = eval_expression(expr.right, row, tables)
        if a == nil or b == nil then return nil end
        local cmp = types.compare(a, b)
        if cmp == nil then return nil end
        local op = expr.op
        if op == 71 then return cmp == 0
        elseif op == 72 then return cmp ~= 0
        elseif op == 73 then return cmp < 0
        elseif op == 74 then return cmp > 0
        elseif op == 75 then return cmp <= 0
        elseif op == 76 then return cmp >= 0
        else return nil
        end
    elseif etype == "IS NULL" then
        local a = eval_expression(expr.expr, row, tables)
        return a == nil
    elseif etype == "IS NOT NULL" then
        local a = eval_expression(expr.expr, row, tables)
        return a ~= nil
    elseif etype == "LIKE" then
        local a = eval_expression(expr.expr, row, tables)
        local pattern = eval_expression(expr.pattern, row, tables)
        if a == nil or pattern == nil then return nil end
        local str_a = types.to_text(a)
        local str_p = types.to_text(pattern)
        if str_a == nil or str_p == nil then return nil end
        local lua_pattern = str_p:gsub("%%", ".*"):gsub("_", ".")
        return string.match(str_a, "^" .. lua_pattern .. "$") ~= nil
    elseif etype == "IN" then
        local a = eval_expression(expr.expr, row, tables)
        if a == nil then return nil end
        for _, v in ipairs(expr.values) do
            local val = eval_expression(v, row, tables)
            if types.equals(a, val) then return true end
        end
        return false
    elseif etype == "BETWEEN" then
        local a = eval_expression(expr.expr, row, tables)
        local low = eval_expression(expr.low, row, tables)
        local high = eval_expression(expr.high, row, tables)
        if a == nil or low == nil or high == nil then return nil end
        return types.greater_equal(a, low) and types.less_equal(a, high)
    end
    return nil
end
local function eval_aggregate(func_name, values)
    if func_name == "COUNT" then
        if values[1] == "*" then
            return #values
        end
        local count = 0
        for _, v in ipairs(values) do
            if v ~= nil then count = count + 1 end
        end
        return count
    elseif func_name == "SUM" then
        local sum = 0
        local has_value = false
        for _, v in ipairs(values) do
            if v ~= nil then
                local num = types.to_number(v)
                if num then
                    sum = sum + num
                    has_value = true
                end
            end
        end
        return has_value and sum or nil
    elseif func_name == "AVG" then
        local sum = 0
        local count = 0
        for _, v in ipairs(values) do
            if v ~= nil then
                local num = types.to_number(v)
                if num then
                    sum = sum + num
                    count = count + 1
                end
            end
        end
        return count > 0 and (sum / count) or nil
    elseif func_name == "MIN" then
        local min_val = nil
        for _, v in ipairs(values) do
            if v ~= nil then
                if min_val == nil or types.compare(v, min_val) < 0 then
                    min_val = v
                end
            end
        end
        return min_val
    elseif func_name == "MAX" then
        local max_val = nil
        for _, v in ipairs(values) do
            if v ~= nil then
                if max_val == nil or types.compare(v, max_val) > 0 then
                    max_val = v
                end
            end
        end
        return max_val
    end
    return nil
end
local function eval_scalar(func_name, args)
    if func_name == "UPPER" then
        local v = args[1]
        if v == nil then return nil end
        return string.upper(types.to_text(v))
    elseif func_name == "LOWER" then
        local v = args[1]
        if v == nil then return nil end
        return string.lower(types.to_text(v))
    elseif func_name == "TRIM" then
        local v = args[1]
        if v == nil then return nil end
        return string.gsub(types.to_text(v), "^%s*(.-)%s*$", "%1")
    elseif func_name == "LENGTH" then
        local v = args[1]
        if v == nil then return nil end
        return #types.to_text(v)
    elseif func_name == "SUBSTR" then
        local v = args[1]
        if v == nil then return nil end
        local str = types.to_text(v)
        local start = types.to_integer(args[2])
        local len = types.to_integer(args[3])
        if len then
            return str:sub(start, start + len - 1)
        else
            return str:sub(start)
        end
    elseif func_name == "ABS" then
        local v = args[1]
        if v == nil then return nil end
        local num = types.to_number(v)
        if num == nil then return nil end
        return math.abs(num)
    elseif func_name == "CEIL" then
        local v = args[1]
        if v == nil then return nil end
        local num = types.to_number(v)
        if num == nil then return nil end
        return math.ceil(num)
    elseif func_name == "FLOOR" then
        local v = args[1]
        if v == nil then return nil end
        local num = types.to_number(v)
        if num == nil then return nil end
        return math.floor(num)
    elseif func_name == "ROUND" then
        local v = args[1]
        if v == nil then return nil end
        local num = types.to_number(v)
        if num == nil then return nil end
        local digits = args[2] and types.to_integer(args[2]) or 0
        local factor = 10 ^ digits
        return math.floor(num * factor + 0.5) / factor
    elseif func_name == "CONCAT" then
        local result = ""
        for _, v in ipairs(args) do
            if v ~= nil then
                result = result .. types.to_text(v)
            end
        end
        return result
    elseif func_name == "COALESCE" then
        for _, v in ipairs(args) do
            if v ~= nil then return v end
        end
        return nil
    elseif func_name == "IFNULL" then
        if args[1] ~= nil then return args[1] end
        return args[2]
    end
    return nil
end
local function resolve_column(expr, row, table_context)
    if expr.type ~= "COLUMN" then
        return eval_expression(expr, row, table_context)
    end
    local table_alias = expr.table
    local col_name = expr.column
    if table_alias then
        for _, t in ipairs(table_context) do
            if t.alias == table_alias or t.name == table_alias then
                local idx = t.table:get_column_index(col_name)
                if idx then
                    return row[t.row_offset + idx]
                end
            end
        end
    else
        for _, t in ipairs(table_context) do
            local idx = t.table:get_column_index(col_name)
            if idx then
                return row[t.row_offset + idx]
            end
        end
    end
    return nil
end
local function evaluate_where(where_expr, row, table_context)
    if not where_expr then return true end
    local result = eval_expression(where_expr, row, table_context)
    if result == nil then return false end
    return result == true
end
local function execute_select(stmt, db)
    local result_rows = {}
    local result_columns = {}
    local table_context = {}
    if stmt.from then
        for _, table_ref in ipairs(stmt.from.tables) do
            local t = db:get_table(table_ref.name)
            if not t then
                error("no such table: " .. table_ref.name)
            end
            table.insert(table_context, {
                name = table_ref.name,
                alias = table_ref.alias or table_ref.name,
                table = t,
                row_offset = 0,
            })
        end
    end
    local function get_cross_product(rows_list, index)
        if index > #rows_list then
            return {{}}
        end
        local result = {}
        local current_rows = rows_list[index]
        local rest = get_cross_product(rows_list, index + 1)
        for _, row in ipairs(current_rows) do
            for _, rest_row in ipairs(rest) do
                local combined = {}
                for _, v in ipairs(row) do
                    table.insert(combined, v)
                end
                for _, v in ipairs(rest_row) do
                    table.insert(combined, v)
                end
                table.insert(result, combined)
            end
        end
        return result
    end
    if #table_context > 0 then
        local all_rows = {}
        for _, tc in ipairs(table_context) do
            local rows = {}
            for _, row in ipairs(tc.table.rows) do
                local row_copy = {}
                for i = 1, #tc.table.columns do
                    row_copy[i] = row[i]
                end
                table.insert(rows, row_copy)
            end
            table.insert(all_rows, rows)
        end
        local joined_rows = all_rows[1]
        for i = 2, #all_rows do
            local new_rows = {}
            for _, left_row in ipairs(joined_rows) do
                for _, right_row in ipairs(all_rows[i]) do
                    local combined = {}
                    for _, v in ipairs(left_row) do
                        table.insert(combined, v)
                    end
                    for _, v in ipairs(right_row) do
                        table.insert(combined, v)
                    end
                    table.insert(new_rows, combined)
                end
            end
            joined_rows = new_rows
        end
        local offset = 0
        for i, tc in ipairs(table_context) do
            tc.row_offset = offset
            offset = offset + #tc.table.columns
        end
        for _, row in ipairs(joined_rows) do
            if evaluate_where(stmt.where, row, table_context) then
                table.insert(result_rows, row)
            end
        end
    end
    if #stmt.columns > 0 and stmt.columns[1].star then
        for _, tc in ipairs(table_context) do
            for i, col in ipairs(tc.table.columns) do
                table.insert(result_columns, {
                    name = col.name,
                    table = tc.alias,
                    index = tc.row_offset + i,
                })
            end
        end
    else
        for _, col_def in ipairs(stmt.columns) do
            if col_def.expr.type == "COLUMN" then
                table.insert(result_columns, {
                    name = col_def.expr.column,
                    type = "COLUMN",
                    column = col_def.expr.column,
                    table = col_def.expr.table,
                    index = nil,
                })
            elseif col_def.expr.type == "LITERAL" then
                table.insert(result_columns, {
                    name = "expr",
                    table = nil,
                    index = nil,
                    literal = col_def.expr.value,
                })
            end
        end
    end
    local final_rows = {}
    for _, row in ipairs(result_rows) do
        local result_row = {}
        for i, col in ipairs(result_columns) do
            if col.literal ~= nil then
                result_row[i] = col.literal
            elseif col.index then
                result_row[i] = row[col.index]
            else
                result_row[i] = resolve_column(col, row, table_context)
            end
        end
        table.insert(final_rows, result_row)
    end
    if stmt.unions then
        local function row_seen(needle)
            for _, existing in ipairs(final_rows) do
                local same = #existing == #needle
                if same then
                    for i, v in ipairs(needle) do
                        if not types.equals(existing[i], v) then
                            same = false
                            break
                        end
                    end
                end
                if same then return true end
            end
            return false
        end
        for _, union in ipairs(stmt.unions) do
            local sub = execute_select(union.select, db)
            for _, row in ipairs(sub.rows) do
                if union.all or not row_seen(row) then
                    table.insert(final_rows, row)
                end
            end
        end
    end
    if stmt.limit then
        local offset_val = 0
        if stmt.limit.offset then
            offset_val = types.to_integer(eval_expression(stmt.limit.offset, {}, table_context)) or 0
        end
        local limit_val = types.to_integer(eval_expression(stmt.limit.limit, {}, table_context)) or -1
        if offset_val > 0 then
            local new_rows = {}
            for i = offset_val + 1, #final_rows do
                table.insert(new_rows, final_rows[i])
            end
            final_rows = new_rows
        end
        if limit_val >= 0 then
            local new_rows = {}
            for i = 1, math.min(limit_val, #final_rows) do
                table.insert(new_rows, final_rows[i])
            end
            final_rows = new_rows
        end
    end
    if stmt.order_by then
        table.sort(final_rows, function(a, b)
            for _, ob in ipairs(stmt.order_by) do
                local av = a[result_columns_index(result_columns, ob.expr)]
                local bv = b[result_columns_index(result_columns, ob.expr)]
                local cmp = types.compare(av, bv)
                if cmp == nil then cmp = 0 end
                if cmp ~= 0 then
                    if ob.desc then
                        return cmp > 0
                    else
                        return cmp < 0
                    end
                end
            end
            return false
        end)
    end
    local column_names = {}
    for _, col in ipairs(result_columns) do
        if col.name then
            table.insert(column_names, col.alias or col.name)
        else
            table.insert(column_names, col.alias or "expr")
        end
    end
    return {columns = column_names, rows = final_rows}
end
function result_columns_index(result_columns, expr)
    for i, col in ipairs(result_columns) do
        if col.name == expr.column then
            return i
        end
    end
    return 1
end
local function execute_insert(stmt, db)
    local tbl = db:get_table(stmt.table)
    if not tbl then
        error("no such table: " .. stmt.table)
    end
    local row_data = {}
    if stmt.values then
        if #stmt.columns > 0 then
            for i, col_name in ipairs(stmt.columns) do
                local idx = tbl:get_column_index(col_name)
                if idx then
                    local val = nil
                    if stmt.values[i] and stmt.values[i].type == "LITERAL" then
                        val = stmt.values[i].value
                    end
                    row_data[col_name] = val
                end
            end
        else
            for i, col in ipairs(tbl.columns) do
                local val = nil
                if stmt.values[i] and stmt.values[i].type == "LITERAL" then
                    val = stmt.values[i].value
                end
                row_data[col.name] = val
            end
        end
    elseif stmt.select then
        local select_result = execute_select(stmt.select, db)
        for _, row in ipairs(select_result.rows) do
            local row_data = {}
            for i, col in ipairs(tbl.columns) do
                if i <= #select_result.columns then
                    row_data[col.name] = row[i]
                end
            end
            tbl:add_row(row_data)
        end
        return
    end
    tbl:add_row(row_data)
end
local function execute_update(stmt, db)
    local tbl = db:get_table(stmt.table)
    if not tbl then
        error("no such table: " .. stmt.table)
    end
    local table_context = {{name = stmt.table, alias = stmt.table, table = tbl, row_offset = 0}}
    local updated = 0
    for i = #tbl.rows, 1, -1 do
        local row = tbl.rows[i]
        if evaluate_where(stmt.where, row, table_context) then
            for _, assignment in ipairs(stmt.set) do
                local idx = tbl:get_column_index(assignment.column)
                if idx then
                    local val = eval_expression(assignment.value, row, table_context)
                    row[idx] = val
                end
            end
            updated = updated + 1
        end
    end
    return updated
end
local function execute_delete(stmt, db)
    local tbl = db:get_table(stmt.table)
    if not tbl then
        error("no such table: " .. stmt.table)
    end
    local table_context = {{name = stmt.table, alias = stmt.table, table = tbl, row_offset = 0}}
    local deleted = 0
    for i = #tbl.rows, 1, -1 do
        local row = tbl.rows[i]
        if evaluate_where(stmt.where, row, table_context) then
            tbl:delete_row(i)
            deleted = deleted + 1
        end
    end
    return deleted
end
local function execute_create(stmt, db)
    if db:has_table(stmt.table) then
        if stmt.if_not_exists then
            return
        end
        error("table " .. stmt.table .. " already exists")
    end
    local columns = {}
    for _, col_def in ipairs(stmt.columns) do
        table.insert(columns, {
            name = col_def.name,
            type = col_def.type,
            not_null = col_def.not_null,
            default_value = col_def.default_value,
            primary_key = col_def.primary_key,
            unique = col_def.unique,
        })
    end
    db:create_table(stmt.table, columns)
end
local function execute_drop(stmt, db)
    if not db:has_table(stmt.table) then
        if stmt.if_exists then
            return
        end
        error("no such table: " .. stmt.table)
    end
    db:drop_table(stmt.table)
end
local function execute_alter(stmt, db)
    local tbl = db:get_table(stmt.table)
    if not tbl then
        error("no such table: " .. stmt.table)
    end
    if stmt.add_column then
        tbl:add_column(
            stmt.add_column.name,
            stmt.add_column.type,
            stmt.add_column.not_null,
            stmt.add_column.default_value,
            stmt.add_column.primary_key,
            stmt.add_column.unique
        )
    end
end
function M.execute(statements, db)
    local results = {}
    for _, stmt in ipairs(statements) do
        if stmt.type == "SELECT" then
            table.insert(results, execute_select(stmt, db))
        elseif stmt.type == "INSERT" then
            execute_insert(stmt, db)
            table.insert(results, {inserted = true})
        elseif stmt.type == "UPDATE" then
            local count = execute_update(stmt, db)
            table.insert(results, {updated = count})
        elseif stmt.type == "DELETE" then
            local count = execute_delete(stmt, db)
            table.insert(results, {deleted = count})
        elseif stmt.type == "CREATE" then
            execute_create(stmt, db)
            table.insert(results, {created = true})
        elseif stmt.type == "DROP" then
            execute_drop(stmt, db)
            table.insert(results, {dropped = true})
        elseif stmt.type == "ALTER" then
            execute_alter(stmt, db)
            table.insert(results, {altered = true})
        elseif stmt.type == "BEGIN" then
            table.insert(results, {begin = true})
        elseif stmt.type == "COMMIT" then
            table.insert(results, {commit = true})
        elseif stmt.type == "ROLLBACK" then
            table.insert(results, {rollback = true})
        end
    end
    return results
end
return M
