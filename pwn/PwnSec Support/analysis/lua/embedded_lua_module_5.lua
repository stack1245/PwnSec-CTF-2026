local M = {}
M.TYPE_NULL = "NULL"
M.TYPE_INTEGER = "INTEGER"
M.TYPE_REAL = "REAL"
M.TYPE_TEXT = "TEXT"
M.TYPE_BLOB = "BLOB"
M.TYPE_NUMERIC = "NUMERIC"
M.AFFINITY_INTEGER = "INTEGER"
M.AFFINITY_REAL = "REAL"
M.AFFINITY_TEXT = "TEXT"
M.AFFINITY_BLOB = "BLOB"
M.AFFINITY_NUMERIC = "NUMERIC"
function M.affinity_from_type(type_name)
    if not type_name then return M.AFFINITY_BLOB end
    local t = string.upper(type_name)
    if string.find(t, "INT") then return M.AFFINITY_INTEGER end
    if string.find(t, "CHAR") or string.find(t, "CLOB") or string.find(t, "TEXT") then
        return M.AFFINITY_TEXT
    end
    if string.find(t, "BLOB") or string.find(t, "NONE") then
        return M.AFFINITY_BLOB
    end
    if string.find(t, "REAL") or string.find(t, "FLOA") or string.find(t, "DOUB") then
        return M.AFFINITY_REAL
    end
    return M.AFFINITY_NUMERIC
end
function M.is_null(value)
    return value == nil or value == M.TYPE_NULL
end
function M.value_type(value)
    if value == nil or value == M.TYPE_NULL then return M.TYPE_NULL end
    if type(value) == "number" then
        if math.floor(value) == value then
            return M.TYPE_INTEGER
        else
            return M.TYPE_REAL
        end
    end
    if type(value) == "string" then return M.TYPE_TEXT end
    if type(value) == "boolean" then return M.TYPE_INTEGER end
    return M.TYPE_BLOB
end
function M.apply_affinity(value, affinity)
    if value == nil or value == M.TYPE_NULL then return value end
    if affinity == M.AFFINITY_INTEGER then
        if type(value) == "string" then
            local num = tonumber(value)
            if num and math.floor(num) == num then
                return math.floor(num)
            end
            return value
        elseif type(value) == "number" then
            if math.floor(value) == value then
                return math.floor(value)
            end
            return value
        end
    elseif affinity == M.AFFINITY_REAL then
        if type(value) == "string" then
            return tonumber(value) or value
        elseif type(value) == "number" then
            return value
        end
    elseif affinity == M.AFFINITY_TEXT then
        if type(value) == "number" then
            return tostring(value)
        end
    end
    return value
end
function M.to_text(value)
    if value == nil or value == M.TYPE_NULL then return nil end
    if type(value) == "string" then return value end
    if type(value) == "number" then
        if math.floor(value) == value then
            return tostring(math.floor(value))
        else
            return tostring(value)
        end
    end
    if type(value) == "boolean" then
        return value and "1" or "0"
    end
    return tostring(value)
end
function M.to_number(value)
    if value == nil or value == M.TYPE_NULL then return nil end
    if type(value) == "number" then return value end
    if type(value) == "string" then
        return tonumber(value)
    end
    return nil
end
function M.to_integer(value)
    if value == nil or value == M.TYPE_NULL then return nil end
    if type(value) == "number" then
        return math.floor(value)
    end
    if type(value) == "string" then
        local num = tonumber(value)
        if num then return math.floor(num) end
    end
    return nil
end
function M.compare(a, b)
    if a == nil or a == M.TYPE_NULL then
        if b == nil or b == M.TYPE_NULL then
            return 0
        end
        return nil
    end
    if b == nil or b == M.TYPE_NULL then
        return nil
    end
    local ta = type(a)
    local tb = type(b)
    if ta == "number" and tb == "number" then
        if a < b then return -1 end
        if a > b then return 1 end
        return 0
    elseif ta == "string" and tb == "string" then
        if a < b then return -1 end
        if a > b then return 1 end
        return 0
    else
        local na = M.to_number(a)
        local nb = M.to_number(b)
        if na and nb then
            if na < nb then return -1 end
            if na > nb then return 1 end
            return 0
        end
        local sa = M.to_text(a)
        local sb = M.to_text(b)
        if sa and sb then
            if sa < sb then return -1 end
            if sa > sb then return 1 end
            return 0
        end
        return 0
    end
end
function M.equals(a, b)
    local result = M.compare(a, b)
    if result == nil then return nil end
    return result == 0
end
function M.not_equals(a, b)
    local result = M.compare(a, b)
    if result == nil then return nil end
    return result ~= 0
end
function M.less_than(a, b)
    local result = M.compare(a, b)
    if result == nil then return nil end
    return result < 0
end
function M.less_equal(a, b)
    local result = M.compare(a, b)
    if result == nil then return nil end
    return result <= 0
end
function M.greater_than(a, b)
    local result = M.compare(a, b)
    if result == nil then return nil end
    return result > 0
end
function M.greater_equal(a, b)
    local result = M.compare(a, b)
    if result == nil then return nil end
    return result >= 0
end
function M.to_display(value)
    if value == nil or value == M.TYPE_NULL then return "NULL" end
    if type(value) == "number" then
        if math.floor(value) == value then
            return tostring(math.floor(value))
        else
            return tostring(value)
        end
    end
    return tostring(value)
end
return M
