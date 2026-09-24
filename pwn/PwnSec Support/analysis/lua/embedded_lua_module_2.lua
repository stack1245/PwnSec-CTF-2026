local types = require("sql.types")
local storage = require("sql.storage")
local engine = require("sql.engine")
local M = {}
function M.create_database()
    local db = storage:new()
    db:create_table("users", {
        {name = "id", type = "INTEGER", primary_key = true, not_null = true},
        {name = "username", type = "TEXT", unique = true, not_null = true},
        {name = "password", type = "TEXT", not_null = true},
        {name = "is_admin", type = "INTEGER", default_value = 0},
        {name = "created_at", type = "TEXT"},
    })
    db:create_table("tickets", {
        {name = "id", type = "INTEGER", primary_key = true, not_null = true},
        {name = "title", type = "TEXT", not_null = true},
        {name = "description", type = "TEXT"},
        {name = "reporter_id", type = "INTEGER"},
        {name = "status", type = "TEXT", default_value = "OPEN"},
        {name = "priority", type = "INTEGER", default_value = 0},
        {name = "created_at", type = "TEXT"},
        {name = "resolution", type = "TEXT"},
    })
    db:create_table("sessions", {
        {name = "token", type = "TEXT", primary_key = true, not_null = true},
        {name = "user_id", type = "INTEGER"},
        {name = "expires_at", type = "TEXT"},
        {name = "ip_address", type = "TEXT"},
    })
    db:create_table("flags", {
        {name = "id", type = "INTEGER", primary_key = true, not_null = true},
        {name = "flag_value", type = "TEXT", not_null = true},
    })
    local root_password = rand_hex(64)
    db:insert("users", {
        id = 1,
        username = "root",
        password = root_password,
        is_admin = 1,
        created_at = "2026-01-01 00:00:00",
    })
    db:insert("users", {
        id = 2,
        username = "agent_bot",
        password = rand_hex(64),
        is_admin = 0,
        created_at = "2026-01-15 10:30:00",
    })
    db:insert("users", {
        id = 3,
        username = "tier1",
        password = rand_hex(64),
        is_admin = 0,
        created_at = "2026-02-02 08:00:00",
    })
    db:insert("tickets", {
        id = 1,
        title = "L3afVM refuses to power off",
        description = "We issued HLT and exit(0). The VM acknowledged both and kept serving HTTP. "
            .. "We would like it to stop. We would also like to know if it is still running. Please advise.",
        reporter_id = 1,
        status = "OPEN",
        priority = 5,
        created_at = "2026-07-31 09:12:00",
        resolution = "",
    })
    db:insert("tickets", {
        id = 2,
        title = "Docs request: everything",
        description = "This portal runs on a virtual machine we cannot find documentation for. "
            .. "Requesting the manual, the source, the README, a README, literally anything. Please advise.",
        reporter_id = 2,
        status = "WONTFIX",
        priority = 2,
        created_at = "2026-07-30 18:03:00",
        resolution = "Closed as WONTFIX. There is no documentation. There never was.",
    })
    db:insert("tickets", {
        id = 3,
        title = "The heap ate my homework",
        description = "malloc returned my homework as a 64-byte buffer with an 8-byte header. "
            .. "It has been zeroed. I would like it back. I know it is somewhere in 128 MiB. Please advise.",
        reporter_id = 3,
        status = "LOST",
        priority = 3,
        created_at = "2026-07-29 22:41:00",
        resolution = "We searched the heap. It is no longer in the heap.",
    })
    db:insert("tickets", {
        id = 4,
        title = "Registers reset on reboot",
        description = "Every HLT zeroes all 256 registers. We were storing our precious flag in R7. "
            .. "It is gone now. Is there a backup? There was no backup. Please advise.",
        reporter_id = 1,
        status = "OPEN",
        priority = 4,
        created_at = "2026-07-28 11:20:00",
        resolution = "",
    })
    db:insert("tickets", {
        id = 5,
        title = "The clock says 2024",
        description = "The VM insists today is 2024. Our countdown to launch has been stuck "
            .. "for two years. We are fairly sure it is 2026. Please advise.",
        reporter_id = 2,
        status = "NEVER",
        priority = 1,
        created_at = "2026-07-27 07:55:00",
        resolution = "Assigned to nobody. Reopened twice. We no longer discuss the clock.",
    })
    return db
end
function M.query(db, sql)
    local parser = require("sql.parser")
    local statements = parser.parse(sql)
    return engine.execute(statements, db)
end
function M.format_results(results)
    local output = {}
    for i, result in ipairs(results) do
        if result.columns then
            table.insert(output, "Result " .. i .. ":")
            local col_names = table.concat(result.columns, " | ")
            table.insert(output, col_names)
            table.insert(output, string.rep("-", #col_names))
            for _, row in ipairs(result.rows) do
                local values = {}
                for _, v in ipairs(row) do
                    if v == nil then
                        table.insert(values, "NULL")
                    else
                        table.insert(values, types.to_display(v))
                    end
                end
                table.insert(output, table.concat(values, " | "))
            end
        elseif result.inserted then
            table.insert(output, "INSERT: 1 row affected")
        elseif result.updated then
            table.insert(output, "UPDATE: " .. result.updated .. " rows affected")
        elseif result.deleted then
            table.insert(output, "DELETE: " .. result.deleted .. " rows affected")
        elseif result.created then
            table.insert(output, "CREATE TABLE")
        elseif result.dropped then
            table.insert(output, "DROP TABLE")
        elseif result.altered then
            table.insert(output, "ALTER TABLE")
        end
    end
    return table.concat(output, "\n")
end
return M
