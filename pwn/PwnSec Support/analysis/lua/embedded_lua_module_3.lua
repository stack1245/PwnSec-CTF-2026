local types = require("sql.types")
local M = {}
local TOK_SELECT = 1
local TOK_FROM = 2
local TOK_WHERE = 3
local TOK_INSERT = 4
local TOK_INTO = 5
local TOK_VALUES = 6
local TOK_UPDATE = 7
local TOK_SET = 8
local TOK_DELETE = 9
local TOK_CREATE = 10
local TOK_TABLE = 11
local TOK_DROP = 12
local TOK_ALTER = 13
local TOK_ADD = 14
local TOK_AND = 15
local TOK_OR = 16
local TOK_NOT = 17
local TOK_NULL = 18
local TOK_IS = 19
local TOK_IN = 20
local TOK_BETWEEN = 21
local TOK_LIKE = 22
local TOK_AS = 23
local TOK_ON = 24
local TOK_JOIN = 25
local TOK_INNER = 26
local TOK_LEFT = 27
local TOK_RIGHT = 28
local TOK_FULL = 29
local TOK_OUTER = 30
local TOK_CROSS = 31
local TOK_GROUP = 32
local TOK_ORDER = 33
local TOK_BY = 34
local TOK_HAVING = 35
local TOK_LIMIT = 36
local TOK_OFFSET = 37
local TOK_UNION = 38
local TOK_ALL = 39
local TOK_DISTINCT = 40
local TOK_INTERSECT = 41
local TOK_EXCEPT = 42
local TOK_BEGIN = 43
local TOK_COMMIT = 44
local TOK_ROLLBACK = 45
local TOK_SAVEPOINT = 46
local TOK_INTEGER = 47
local TOK_TEXT = 48
local TOK_REAL = 49
local TOK_BLOB = 50
local TOK_NUMERIC = 51
local TOK_PRIMARY = 52
local TOK_KEY = 53
local TOK_FOREIGN = 54
local TOK_REFERENCES = 55
local TOK_UNIQUE = 56
local TOK_CHECK = 57
local TOK_DEFAULT = 58
local TOK_AUTOINCREMENT = 59
local TOK_IF = 60
local TOK_EXISTS = 61
local TOK_STRING = 62
local TOK_NUMBER = 63
local TOK_IDENTIFIER = 64
local TOK_LPAREN = 65
local TOK_RPAREN = 66
local TOK_COMMA = 67
local TOK_SEMICOLON = 68
local TOK_DOT = 69
local TOK_STAR = 70
local TOK_EQ = 71
local TOK_NE = 72
local TOK_LT = 73
local TOK_GT = 74
local TOK_LE = 75
local TOK_GE = 76
local TOK_PLUS = 77
local TOK_MINUS = 78
local TOK_TIMES = 79
local TOK_DIVIDE = 80
local TOK_MOD = 81
local TOK_ASSIGN = 82
local TOK_DOTDOT = 83
local TOK_EOF = 84
local function tokenize(sql)
    local tokens = {}
    local pos = 1
    local len = #sql
    local function skip_whitespace()
        while pos <= len do
            local c = sql:sub(pos, pos)
            if c == " " or c == "\t" or c == "\n" or c == "\r" then
                pos = pos + 1
            elseif sql:sub(pos, pos + 1) == "--" then
                while pos <= len and sql:sub(pos, pos) ~= "\n" do
                    pos = pos + 1
                end
            elseif sql:sub(pos, pos + 1) == "/*" then
                pos = pos + 2
                while pos <= len and sql:sub(pos, pos + 1) ~= "*/" do
                    pos = pos + 1
                end
                pos = pos + 2
            else
                break
            end
        end
    end
    local function read_string()
        local quote = sql:sub(pos, pos)
        pos = pos + 1
        local result = ""
        while pos <= len do
            local c = sql:sub(pos, pos)
            if c == quote then
                pos = pos + 1
                return result
            elseif c == "\\" then
                pos = pos + 1
                local next_c = sql:sub(pos, pos)
                if next_c == "n" then result = result .. "\n"
                elseif next_c == "t" then result = result .. "\t"
                elseif next_c == "r" then result = result .. "\r"
                elseif next_c == "'" then result = result .. "'"
                elseif next_c == '"' then result = result .. '"'
                elseif next_c == "\\" then result = result .. "\\"
                else result = result .. next_c end
                pos = pos + 1
            else
                result = result .. c
                pos = pos + 1
            end
        end
        error("Unterminated string")
    end
    local function read_number()
        local start = pos
        while pos <= len do
            local c = sql:sub(pos, pos)
            if (c >= "0" and c <= "9") or c == "." or c == "e" or c == "E" or c == "+" or c == "-" then
                pos = pos + 1
            else
                break
            end
        end
        return tonumber(sql:sub(start, pos - 1))
    end
    local function read_identifier()
        local start = pos
        while pos <= len do
            local c = sql:sub(pos, pos)
            if (c >= "a" and c <= "z") or (c >= "A" and c <= "Z") or (c >= "0" and c <= "9") or c == "_" then
                pos = pos + 1
            else
                break
            end
        end
        return sql:sub(start, pos - 1)
    end
    local keywords = {
        ["SELECT"] = TOK_SELECT, ["FROM"] = TOK_FROM, ["WHERE"] = TOK_WHERE,
        ["INSERT"] = TOK_INSERT, ["INTO"] = TOK_INTO, ["VALUES"] = TOK_VALUES,
        ["UPDATE"] = TOK_UPDATE, ["SET"] = TOK_SET, ["DELETE"] = TOK_DELETE,
        ["CREATE"] = TOK_CREATE, ["TABLE"] = TOK_TABLE, ["DROP"] = TOK_DROP,
        ["ALTER"] = TOK_ALTER, ["ADD"] = TOK_ADD, ["AND"] = TOK_AND,
        ["OR"] = TOK_OR, ["NOT"] = TOK_NOT, ["NULL"] = TOK_NULL,
        ["IS"] = TOK_IS, ["IN"] = TOK_IN, ["BETWEEN"] = TOK_BETWEEN,
        ["LIKE"] = TOK_LIKE, ["AS"] = TOK_AS, ["ON"] = TOK_ON,
        ["JOIN"] = TOK_JOIN, ["INNER"] = TOK_INNER, ["LEFT"] = TOK_LEFT,
        ["RIGHT"] = TOK_RIGHT, ["FULL"] = TOK_FULL, ["OUTER"] = TOK_OUTER,
        ["CROSS"] = TOK_CROSS, ["GROUP"] = TOK_GROUP, ["ORDER"] = TOK_ORDER,
        ["BY"] = TOK_BY, ["HAVING"] = TOK_HAVING, ["LIMIT"] = TOK_LIMIT,
        ["OFFSET"] = TOK_OFFSET, ["UNION"] = TOK_UNION, ["ALL"] = TOK_ALL,
        ["DISTINCT"] = TOK_DISTINCT, ["INTERSECT"] = TOK_INTERSECT,
        ["EXCEPT"] = TOK_EXCEPT, ["BEGIN"] = TOK_BEGIN, ["COMMIT"] = TOK_COMMIT,
        ["ROLLBACK"] = TOK_ROLLBACK, ["SAVEPOINT"] = TOK_SAVEPOINT,
        ["INTEGER"] = TOK_INTEGER, ["TEXT"] = TOK_TEXT, ["REAL"] = TOK_REAL,
        ["BLOB"] = TOK_BLOB, ["NUMERIC"] = TOK_NUMERIC, ["PRIMARY"] = TOK_PRIMARY,
        ["KEY"] = TOK_KEY, ["FOREIGN"] = TOK_FOREIGN, ["REFERENCES"] = TOK_REFERENCES,
        ["UNIQUE"] = TOK_UNIQUE, ["CHECK"] = TOK_CHECK, ["DEFAULT"] = TOK_DEFAULT,
        ["AUTOINCREMENT"] = TOK_AUTOINCREMENT, ["IF"] = TOK_IF, ["EXISTS"] = TOK_EXISTS,
    }
    while true do
        skip_whitespace()
        if pos > len then
            table.insert(tokens, {type = TOK_EOF, value = nil})
            break
        end
        local c = sql:sub(pos, pos)
        local two = sql:sub(pos, pos + 1)
        if c == "'" then
            local str = read_string()
            table.insert(tokens, {type = TOK_STRING, value = str})
        elseif two == "<=" then
            pos = pos + 2
            table.insert(tokens, {type = TOK_LE, value = "<="})
        elseif two == ">=" then
            pos = pos + 2
            table.insert(tokens, {type = TOK_GE, value = ">="})
        elseif two == "!=" then
            pos = pos + 2
            table.insert(tokens, {type = TOK_NE, value = "!="})
        elseif two == "<>" then
            pos = pos + 2
            table.insert(tokens, {type = TOK_NE, value = "<>"})
        elseif two == ".." then
            pos = pos + 2
            table.insert(tokens, {type = TOK_DOTDOT, value = ".."})
        elseif c == "*" then
            pos = pos + 1
            table.insert(tokens, {type = TOK_STAR, value = "*"})
        elseif c == "=" then
            pos = pos + 1
            table.insert(tokens, {type = TOK_EQ, value = "="})
        elseif c == "<" then
            pos = pos + 1
            table.insert(tokens, {type = TOK_LT, value = "<"})
        elseif c == ">" then
            pos = pos + 1
            table.insert(tokens, {type = TOK_GT, value = ">"})
        elseif c == "+" then
            pos = pos + 1
            table.insert(tokens, {type = TOK_PLUS, value = "+"})
        elseif c == "-" then
            pos = pos + 1
            table.insert(tokens, {type = TOK_MINUS, value = "-"})
        elseif c == "/" then
            pos = pos + 1
            table.insert(tokens, {type = TOK_DIVIDE, value = "/"})
        elseif c == "%" then
            pos = pos + 1
            table.insert(tokens, {type = TOK_MOD, value = "%"})
        elseif c == "(" then
            pos = pos + 1
            table.insert(tokens, {type = TOK_LPAREN, value = "("})
        elseif c == ")" then
            pos = pos + 1
            table.insert(tokens, {type = TOK_RPAREN, value = ")"})
        elseif c == "," then
            pos = pos + 1
            table.insert(tokens, {type = TOK_COMMA, value = ","})
        elseif c == ";" then
            pos = pos + 1
            table.insert(tokens, {type = TOK_SEMICOLON, value = ";"})
        elseif c == "." then
            pos = pos + 1
            table.insert(tokens, {type = TOK_DOT, value = "."})
        elseif c == ":" then
            pos = pos + 1
        elseif c == "\"" or c == "[" then
            pos = pos + 1
            local id = read_identifier()
            table.insert(tokens, {type = TOK_IDENTIFIER, value = id})
        elseif c >= "0" and c <= "9" then
            local num = read_number()
            table.insert(tokens, {type = TOK_NUMBER, value = num})
        elseif (c >= "a" and c <= "z") or (c >= "A" and c <= "Z") or c == "_" then
            local id = read_identifier()
            local upper = string.upper(id)
            local tok_type = keywords[upper]
            if tok_type then
                table.insert(tokens, {type = tok_type, value = id})
            else
                table.insert(tokens, {type = TOK_IDENTIFIER, value = id})
            end
        else
            pos = pos + 1
        end
    end
    return tokens
end
local Parser = {}
Parser.__index = Parser
function Parser:new(sql)
    local obj = {
        tokens = tokenize(sql),
        pos = 1,
    }
    setmetatable(obj, self)
    return obj
end
function Parser:peek()
    return self.tokens[self.pos]
end
function Parser:next()
    local tok = self.tokens[self.pos]
    self.pos = self.pos + 1
    return tok
end
function Parser:expect(type)
    local tok = self:peek()
    if tok.type ~= type then
        error("Expected token " .. type .. " but got " .. tok.type)
    end
    return self:next()
end
function Parser:parse()
    local statements = {}
    while self:peek().type ~= TOK_EOF do
        local stmt = self:parse_statement()
        table.insert(statements, stmt)
        if self:peek().type == TOK_SEMICOLON then
            self:next()
        end
    end
    return statements
end
function Parser:parse_statement()
    local tok = self:peek()
    if tok.type == TOK_SELECT then
        return self:parse_select()
    elseif tok.type == TOK_INSERT then
        return self:parse_insert()
    elseif tok.type == TOK_UPDATE then
        return self:parse_update()
    elseif tok.type == TOK_DELETE then
        return self:parse_delete()
    elseif tok.type == TOK_CREATE then
        return self:parse_create()
    elseif tok.type == TOK_DROP then
        return self:parse_drop()
    elseif tok.type == TOK_ALTER then
        return self:parse_alter()
    elseif tok.type == TOK_BEGIN then
        self:next()
        return {type = "BEGIN"}
    elseif tok.type == TOK_COMMIT then
        self:next()
        return {type = "COMMIT"}
    elseif tok.type == TOK_ROLLBACK then
        self:next()
        return {type = "ROLLBACK"}
    else
        error("Unexpected token: " .. tok.value)
    end
end
function Parser:parse_select()
    self:expect(TOK_SELECT)
    local distinct = false
    local tok = self:peek()
    if tok.type == TOK_DISTINCT then
        distinct = true
        self:next()
    elseif tok.type == TOK_ALL then
        self:next()
    end
    local columns = self:parse_column_list()
    local from_clause = nil
    if self:peek().type == TOK_FROM then
        from_clause = self:parse_from()
    end
    local where_clause = nil
    if self:peek().type == TOK_WHERE then
        self:next()
        where_clause = self:parse_expression()
    end
    local group_by = nil
    if self:peek().type == TOK_GROUP then
        self:next()
        self:expect(TOK_BY)
        group_by = self:parse_group_by()
    end
    local having = nil
    if self:peek().type == TOK_HAVING then
        self:next()
        having = self:parse_expression()
    end
    local order_by = nil
    if self:peek().type == TOK_ORDER then
        self:next()
        self:expect(TOK_BY)
        order_by = self:parse_order_by()
    end
    local limit = nil
    if self:peek().type == TOK_LIMIT then
        self:next()
        limit = self:parse_expression()
        if self:peek().type == TOK_OFFSET then
            self:next()
            local offset = self:parse_expression()
            limit = {limit = limit, offset = offset}
        end
    end
    local unions = nil
    while self:peek().type == TOK_UNION do
        self:next()
        local all = false
        if self:peek().type == TOK_ALL then
            all = true
            self:next()
        end
        unions = unions or {}
        table.insert(unions, {all = all, select = self:parse_select()})
    end
    return {
        type = "SELECT",
        distinct = distinct,
        columns = columns,
        from = from_clause,
        where = where_clause,
        group_by = group_by,
        having = having,
        order_by = order_by,
        limit = limit,
        unions = unions,
    }
end
function Parser:parse_column_list()
    local columns = {}
    if self:peek().type == TOK_STAR then
        self:next()
        table.insert(columns, {star = true})
        return columns
    end
    repeat
        local col = self:parse_column()
        table.insert(columns, col)
        if self:peek().type == TOK_COMMA then
            self:next()
        else
            break
        end
    until false
    return columns
end
function Parser:parse_column()
    if self:peek().type == TOK_STAR then
        self:next()
        return {star = true}
    end
    local expr = self:parse_expression()
    local alias = nil
    if self:peek().type == TOK_AS then
        self:next()
        alias = self:expect(TOK_IDENTIFIER).value
    elseif self:peek().type == TOK_IDENTIFIER then
        alias = self:next().value
    end
    return {expr = expr, alias = alias}
end
function Parser:parse_from()
    self:expect(TOK_FROM)
    local tables = {}
    local joins = {}
    local first_table = self:parse_table_reference()
    table.insert(tables, first_table)
    while true do
        local tok = self:peek()
        if tok.type == TOK_COMMA then
            self:next()
            local join_table = self:parse_table_reference()
            table.insert(tables, join_table)
        elseif tok.type == TOK_JOIN or tok.type == TOK_INNER or
           tok.type == TOK_LEFT or tok.type == TOK_RIGHT or
           tok.type == TOK_FULL or tok.type == TOK_CROSS then
            local join_type = "INNER"
            if tok.type == TOK_LEFT then join_type = "LEFT"
            elseif tok.type == TOK_RIGHT then join_type = "RIGHT"
            elseif tok.type == TOK_FULL then join_type = "FULL"
            elseif tok.type == TOK_CROSS then join_type = "CROSS"
            end
            if tok.type == TOK_INNER or tok.type == TOK_LEFT or
               tok.type == TOK_RIGHT or tok.type == TOK_FULL then
                self:next()
                if self:peek().type == TOK_OUTER then self:next() end
                self:expect(TOK_JOIN)
            else
                self:next()
            end
            local join_table = self:parse_table_reference()
            local on_expr = nil
            if self:peek().type == TOK_ON then
                self:next()
                on_expr = self:parse_expression()
            end
            table.insert(joins, {
                type = join_type,
                table = join_table,
                on = on_expr,
            })
        else
            break
        end
    end
    return {tables = tables, joins = joins}
end
function Parser:parse_table_reference()
    local name = self:expect(TOK_IDENTIFIER).value
    local alias = nil
    if self:peek().type == TOK_AS then
        self:next()
        alias = self:expect(TOK_IDENTIFIER).value
    elseif self:peek().type == TOK_IDENTIFIER then
        alias = self:next().value
    end
    return {name = name, alias = alias}
end
function Parser:parse_group_by()
    local columns = {}
    repeat
        local col = self:parse_column()
        table.insert(columns, col)
        if self:peek().type == TOK_COMMA then
            self:next()
        else
            break
        end
    until false
    return columns
end
function Parser:parse_order_by()
    local columns = {}
    repeat
        local col = self:parse_expression()
        local desc = false
        if self:peek().type == TOK_IDENTIFIER then
            local dir = string.upper(self:peek().value)
            if dir == "DESC" then
                desc = true
                self:next()
            elseif dir == "ASC" then
                self:next()
            end
        end
        table.insert(columns, {expr = col, desc = desc})
        if self:peek().type == TOK_COMMA then
            self:next()
        else
            break
        end
    until false
    return columns
end
function Parser:parse_insert()
    self:expect(TOK_INSERT)
    self:expect(TOK_INTO)
    local table_name = self:expect(TOK_IDENTIFIER).value
    local columns = {}
    if self:peek().type == TOK_LPAREN then
        self:next()
        repeat
            table.insert(columns, self:expect(TOK_IDENTIFIER).value)
            if self:peek().type == TOK_COMMA then
                self:next()
            else
                break
            end
        until false
        self:expect(TOK_RPAREN)
    end
    if self:peek().type == TOK_VALUES then
        self:next()
        local values = {}
        self:expect(TOK_LPAREN)
        repeat
            local val = self:parse_expression()
            table.insert(values, val)
            if self:peek().type == TOK_COMMA then
                self:next()
            else
                break
            end
        until false
        self:expect(TOK_RPAREN)
        return {type = "INSERT", table = table_name, columns = columns, values = values}
    else
        local select_stmt = self:parse_select()
        return {type = "INSERT", table = table_name, columns = columns, select = select_stmt}
    end
end
function Parser:parse_update()
    self:expect(TOK_UPDATE)
    local table_name = self:expect(TOK_IDENTIFIER).value
    self:expect(TOK_SET)
    local assignments = {}
    repeat
        local col = self:expect(TOK_IDENTIFIER).value
        self:expect(TOK_ASSIGN)
        local val = self:parse_expression()
        table.insert(assignments, {column = col, value = val})
        if self:peek().type == TOK_COMMA then
            self:next()
        else
            break
        end
    until false
    local where_clause = nil
    if self:peek().type == TOK_WHERE then
        self:next()
        where_clause = self:parse_expression()
    end
    return {type = "UPDATE", table = table_name, set = assignments, where = where_clause}
end
function Parser:parse_delete()
    self:expect(TOK_DELETE)
    self:expect(TOK_FROM)
    local table_name = self:expect(TOK_IDENTIFIER).value
    local where_clause = nil
    if self:peek().type == TOK_WHERE then
        self:next()
        where_clause = self:parse_expression()
    end
    return {type = "DELETE", table = table_name, where = where_clause}
end
function Parser:parse_create()
    self:expect(TOK_CREATE)
    if self:peek().type == TOK_TABLE then
        self:next()
        local if_not_exists = false
        if self:peek().type == TOK_IF then
            self:next()
            self:expect(TOK_NOT)
            self:expect(TOK_EXISTS)
            if_not_exists = true
        end
        local table_name = self:expect(TOK_IDENTIFIER).value
        self:expect(TOK_LPAREN)
        local columns = {}
        local constraints = {}
        repeat
            local first = self:peek()
            if first.type == TOK_IDENTIFIER then
                local col = self:parse_column_def()
                table.insert(columns, col)
            else
                local constraint = self:parse_table_constraint()
                table.insert(constraints, constraint)
            end
            if self:peek().type == TOK_COMMA then
                self:next()
            else
                break
            end
        until false
        self:expect(TOK_RPAREN)
        return {type = "CREATE", table = table_name, if_not_exists = if_not_exists,
                columns = columns, constraints = constraints}
    end
    error("Unsupported CREATE")
end
function Parser:parse_column_def()
    local name = self:expect(TOK_IDENTIFIER).value
    local type_name = ""
    local tok = self:peek()
    if tok.type == TOK_INTEGER or tok.type == TOK_TEXT or tok.type == TOK_REAL or
       tok.type == TOK_BLOB or tok.type == TOK_NUMERIC then
        type_name = tok.value
        self:next()
    end
    local not_null = false
    local primary_key = false
    local unique = false
    local default_value = nil
    local auto_increment = false
    while true do
        local tok = self:peek()
        if tok.type == TOK_PRIMARY then
            self:next()
            self:expect(TOK_KEY)
            primary_key = true
        elseif tok.type == TOK_NOT then
            self:next()
            self:expect(TOK_NULL)
            not_null = true
        elseif tok.type == TOK_UNIQUE then
            self:next()
            unique = true
        elseif tok.type == TOK_DEFAULT then
            self:next()
            default_value = self:parse_expression()
        elseif tok.type == TOK_AUTOINCREMENT then
            self:next()
            auto_increment = true
        else
            break
        end
    end
    return {
        name = name,
        type = type_name,
        not_null = not_null,
        primary_key = primary_key,
        unique = unique,
        default_value = default_value,
        auto_increment = auto_increment,
    }
end
function Parser:parse_table_constraint()
    local tok = self:peek()
    if tok.type == TOK_PRIMARY then
        self:next()
        self:expect(TOK_KEY)
        self:expect(TOK_LPAREN)
        local cols = {}
        repeat
            table.insert(cols, self:expect(TOK_IDENTIFIER).value)
            if self:peek().type == TOK_COMMA then self:next() else break end
        until false
        self:expect(TOK_RPAREN)
        return {type = "PRIMARY KEY", columns = cols}
    elseif tok.type == TOK_FOREIGN then
        self:next()
        self:expect(TOK_KEY)
        self:expect(TOK_LPAREN)
        local cols = {}
        repeat
            table.insert(cols, self:expect(TOK_IDENTIFIER).value)
            if self:peek().type == TOK_COMMA then self:next() else break end
        until false
        self:expect(TOK_RPAREN)
        self:expect(TOK_REFERENCES)
        local ref_table = self:expect(TOK_IDENTIFIER).value
        self:expect(TOK_LPAREN)
        local ref_cols = {}
        repeat
            table.insert(ref_cols, self:expect(TOK_IDENTIFIER).value)
            if self:peek().type == TOK_COMMA then self:next() else break end
        until false
        self:expect(TOK_RPAREN)
        return {type = "FOREIGN KEY", columns = cols, references = {table = ref_table, columns = ref_cols}}
    elseif tok.type == TOK_UNIQUE then
        self:next()
        self:expect(TOK_LPAREN)
        local cols = {}
        repeat
            table.insert(cols, self:expect(TOK_IDENTIFIER).value)
            if self:peek().type == TOK_COMMA then self:next() else break end
        until false
        self:expect(TOK_RPAREN)
        return {type = "UNIQUE", columns = cols}
    elseif tok.type == TOK_CHECK then
        self:next()
        self:expect(TOK_LPAREN)
        local expr = self:parse_expression()
        self:expect(TOK_RPAREN)
        return {type = "CHECK", expr = expr}
    end
    error("Unexpected constraint")
end
function Parser:parse_drop()
    self:expect(TOK_DROP)
    self:expect(TOK_TABLE)
    local if_exists = false
    if self:peek().type == TOK_IF then
        self:next()
        self:expect(TOK_EXISTS)
        if_exists = true
    end
    local table_name = self:expect(TOK_IDENTIFIER).value
    return {type = "DROP", table = table_name, if_exists = if_exists}
end
function Parser:parse_alter()
    self:expect(TOK_ALTER)
    self:expect(TOK_TABLE)
    local table_name = self:expect(TOK_IDENTIFIER).value
    self:expect(TOK_ADD)
    local col_def = self:parse_column_def()
    return {type = "ALTER", table = table_name, add_column = col_def}
end
function Parser:parse_expression()
    return self:parse_or()
end
function Parser:parse_or()
    local left = self:parse_and()
    while self:peek().type == TOK_OR do
        self:next()
        local right = self:parse_and()
        left = {type = "OR", left = left, right = right}
    end
    return left
end
function Parser:parse_and()
    local left = self:parse_not()
    while self:peek().type == TOK_AND do
        self:next()
        local right = self:parse_not()
        left = {type = "AND", left = left, right = right}
    end
    return left
end
function Parser:parse_not()
    if self:peek().type == TOK_NOT then
        self:next()
        return {type = "NOT", expr = self:parse_not()}
    end
    return self:parse_comparison()
end
function Parser:parse_comparison()
    local left = self:parse_additive()
    local tok = self:peek()
    if tok.type == TOK_EQ or tok.type == TOK_NE or tok.type == TOK_LT or
       tok.type == TOK_GT or tok.type == TOK_LE or tok.type == TOK_GE then
        self:next()
        local right = self:parse_additive()
        return {type = "COMPARISON", op = tok.type, left = left, right = right}
    elseif tok.type == TOK_IS then
        self:next()
        if self:peek().type == TOK_NOT then
            self:next()
            return {type = "IS NOT NULL", expr = left}
        end
        return {type = "IS NULL", expr = left}
    elseif tok.type == TOK_LIKE then
        self:next()
        local pattern = self:parse_additive()
        return {type = "LIKE", expr = left, pattern = pattern}
    elseif tok.type == TOK_IN then
        self:next()
        if self:peek().type == TOK_LPAREN then
            self:next()
            local values = {}
            repeat
                table.insert(values, self:parse_expression())
                if self:peek().type == TOK_COMMA then
                    self:next()
                else
                    break
                end
            until false
            self:expect(TOK_RPAREN)
            return {type = "IN", expr = left, values = values}
        else
            return {type = "IN", expr = left, values = {}}
        end
    elseif tok.type == TOK_BETWEEN then
        self:next()
        local low = self:parse_additive()
        self:expect(TOK_AND)
        local high = self:parse_additive()
        return {type = "BETWEEN", expr = left, low = low, high = high}
    end
    return left
end
function Parser:parse_additive()
    local left = self:parse_multiplicative()
    while true do
        local tok = self:peek()
        if tok.type == TOK_PLUS then
            self:next()
            local right = self:parse_multiplicative()
            left = {type = "ADD", left = left, right = right}
        elseif tok.type == TOK_MINUS then
            self:next()
            local right = self:parse_multiplicative()
            left = {type = "SUB", left = left, right = right}
        else
            break
        end
    end
    return left
end
function Parser:parse_multiplicative()
    local left = self:parse_unary()
    while true do
        local tok = self:peek()
        if tok.type == TOK_TIMES then
            self:next()
            local right = self:parse_unary()
            left = {type = "MUL", left = left, right = right}
        elseif tok.type == TOK_DIVIDE then
            self:next()
            local right = self:parse_unary()
            left = {type = "DIV", left = left, right = right}
        elseif tok.type == TOK_MOD then
            self:next()
            local right = self:parse_unary()
            left = {type = "MOD", left = left, right = right}
        else
            break
        end
    end
    return left
end
function Parser:parse_unary()
    local tok = self:peek()
    if tok.type == TOK_MINUS then
        self:next()
        return {type = "NEG", expr = self:parse_unary()}
    elseif tok.type == TOK_NOT then
        self:next()
        return {type = "NOT", expr = self:parse_unary()}
    elseif tok.type == TOK_PLUS then
        self:next()
        return self:parse_unary()
    end
    return self:parse_primary()
end
function Parser:parse_primary()
    local tok = self:peek()
    if tok.type == TOK_NUMBER then
        self:next()
        return {type = "LITERAL", value = tok.value}
    elseif tok.type == TOK_STRING then
        self:next()
        return {type = "LITERAL", value = tok.value}
    elseif tok.type == TOK_NULL then
        self:next()
        return {type = "LITERAL", value = nil}
    elseif tok.type == TOK_STAR then
        self:next()
        return {type = "STAR"}
    elseif tok.type == TOK_LPAREN then
        self:next()
        local expr = self:parse_expression()
        self:expect(TOK_RPAREN)
        return expr
    elseif tok.type == TOK_IDENTIFIER then
        self:next()
        if self:peek().type == TOK_DOT then
            self:next()
            local field = self:expect(TOK_IDENTIFIER).value
            return {type = "COLUMN", table = tok.value, column = field}
        end
        return {type = "COLUMN", table = nil, column = tok.value}
    end
    error("Unexpected token in expression: " .. tostring(tok.value))
end
function M.parse(sql)
    local parser = Parser:new(sql)
    return parser:parse()
end
return M
