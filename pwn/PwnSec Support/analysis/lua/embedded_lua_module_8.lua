local tcp_server = require("tcp.server")
local http = require("http.http")
local sql = require("sql")
local css = require("web.style")
local M = {}
local db = nil
local function esc(s)
    if s == nil then return "" end
    s = tostring(s)
    s = s:gsub("&", "&amp;"):gsub("<", "&lt;"):gsub(">", "&gt;"):gsub('"', "&quot;")
    return s
end
local function sql_param(s)
    s = tostring(s or "")
    s = s:gsub("\\", "\\\\"):gsub("'", "\\'")
    return s
end
local function logo_svg()
    return '<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">'
        .. '<rect width="100" height="100" rx="12" fill="#152047"/>'
        .. '<rect x="3" y="3" width="94" height="94" rx="10" fill="none" stroke="#f5c518" stroke-width="3"/>'
        .. '<text x="50" y="38" font-family="monospace" font-size="12" fill="#ffd84d" text-anchor="middle" font-weight="bold">Pwn</text>'
        .. '<text x="50" y="55" font-family="monospace" font-size="12" fill="#ff7a1a" text-anchor="middle" font-weight="bold">Sec</text>'
        .. '<text x="50" y="76" font-family="monospace" font-size="8" fill="#7dffa0" text-anchor="middle">SUPPORT</text>'
        .. '</svg>'
end
local function layout(title, body, active)
    local tabs = {
        { key = "",        label = "Dashboard", href = "/" },
        { key = "tickets", label = "Tickets",   href = "/tickets" },
        { key = "search",  label = "Search",    href = "/search" },
        { key = "login",   label = "Login",     href = "/login" },
    }
    local tabs_html = ""
    for _, tab in ipairs(tabs) do
        local cls = (tab.key == active) and ' class="tab active"' or ' class="tab"'
        tabs_html = tabs_html .. '<a href="' .. tab.href .. '"' .. cls .. '>' .. tab.label .. '</a>'
    end
    return '<!doctype html>\n<html lang="en">\n<head>\n'
        .. '<meta charset="utf-8"/>\n'
        .. '<title>' .. esc(title) .. '</title>\n'
        .. '<meta name="viewport" content="width=device-width, initial-scale=1"/>\n'
        .. '<meta name="description" content="PwnSec Support console — running on a VM you have never heard of."/>\n'
        .. '<meta name="theme-color" content="#0b1226"/>\n'
        .. '<link rel="preconnect" href="https://fonts.googleapis.com"/>\n'
        .. '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>\n'
        .. '<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Space+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet"/>\n'
        .. '<style>\n' .. css .. '\n</style>\n'
        .. '</head>\n<body>\n'
        .. '<div class="wrap">\n'
        .. '<header class="topbar">\n'
        .. '<a class="brand" href="/">'
        .. '<span class="mark">' .. logo_svg() .. '</span>'
        .. '<span><span class="brand-name">PwnSec <b>Support</b></span>'
        .. '<span class="brand-sub">ticket console · ct6-2026</span></span></a>\n'
        .. '</header>\n'
        .. '<nav class="tabs">' .. tabs_html .. '</nav>\n'
        .. body
        .. '</div>\n'
        .. '</body>\n</html>'
end
local function run_query(sql_text)
    local ok, results = pcall(sql.query, db, sql_text)
    if not ok then
        return nil, results
    end
    return results, nil
end
local function badge(status, priority)
    local status_class = tostring(status):lower()
    local out = '<span class="badge ' .. esc(status_class) .. '">' .. esc(status) .. '</span>'
    if priority ~= nil then
        out = out .. ' <span class="badge prio">P' .. esc(priority) .. '</span>'
    end
    return out
end
local function index_page()
    local recent = ""
    local results, err = run_query(
        "SELECT id, title, status, priority FROM tickets ORDER BY priority DESC LIMIT 4")
    if not results then
        recent = '<div class="empty">queue query failed: ' .. esc(err) .. '</div>'
    else
        local rows = ""
        local got = false
        for _, result in ipairs(results) do
            if result.rows then
                got = true
                for _, row in ipairs(result.rows) do
                    rows = rows
                        .. '<tr><td><a href="/ticket?id=' .. esc(row[1]) .. '">#' .. esc(row[1]) .. '</a></td>'
                        .. '<td><a class="tlink" href="/ticket?id=' .. esc(row[1]) .. '">' .. esc(row[2]) .. '</a></td>'
                        .. '<td>' .. badge(row[3], nil) .. '</td>'
                        .. '<td>' .. badge("P" .. tostring(row[4]), nil) .. '</td></tr>'
                end
            end
        end
        if not got then
            rows = '<tr><td colspan="4" class="empty">the queue is empty. that has never happened. something is wrong.</td></tr>'
        end
        recent = '<table class="board"><tr><th>ID</th><th>Title</th><th>Status</th><th>Priority</th></tr>'
            .. rows .. '</table>'
    end
    local body = '<div class="page">\n'
        .. '<div class="page-head">Dashboard</div>\n'
        .. '<div class="page-sub">Welcome to the PwnSec Support console. '
        .. 'We cannot help you, but we did open a ticket about it.</div>\n'
        .. '<div class="panel">\n'
        .. '<div class="panel-title">// recent tickets</div>\n'
        .. recent
        .. '<a class="more" href="/tickets">View the full queue →</a>\n'
        .. '</div>\n'
        .. '</div>\n'
    return layout("PwnSec Support", body, "")
end
local function tickets_page()
    local results, err = run_query("SELECT id, title, status, priority, reporter_id FROM tickets ORDER BY priority DESC")
    local rows = ""
    if not results then
        rows = '<div class="empty">ticket query failed: ' .. esc(err) .. '</div>'
    else
        local got = false
        for _, result in ipairs(results) do
            if result.rows then
                got = true
                for _, row in ipairs(result.rows) do
                    rows = rows
                        .. '<tr><td><a href="/ticket?id=' .. esc(row[1]) .. '">#' .. esc(row[1]) .. '</a></td>'
                        .. '<td><a class="tlink" href="/ticket?id=' .. esc(row[1]) .. '">' .. esc(row[2]) .. '</a></td>'
                        .. '<td>' .. badge(row[3], nil) .. '</td>'
                        .. '<td>' .. badge("P" .. tostring(row[4]), nil) .. '</td>'
                        .. '<td>' .. esc(row[5]) .. '</td></tr>'
                end
            end
        end
        if not got then
            rows = '<div class="empty">the queue is empty. that has never happened. something is wrong.</div>'
        end
    end
    local body = '<div class="page">\n'
        .. '<a class="backlink" href="/">← Back to dashboard</a>\n'
        .. '<div class="page-head">Ticket Queue</div>\n'
        .. '<div class="page-sub">The full queue, straight from the SQL engine. Sorted by priority, highest first. '
        .. 'If your ticket is missing, it was never really there.</div>\n'
        .. '<div class="panel"><table class="board">\n'
        .. '<tr><th>ID</th><th>Title</th><th>Status</th><th>Priority</th><th>Reporter</th></tr>\n'
        .. rows .. '</table></div>\n'
        .. '</div>\n'
    return layout("Ticket Queue — PwnSec Support", body, "tickets")
end
local function ticket_page(request)
    local id = request.query["id"] or ""
    if id == "" then
        return layout("Not Found", '<div class="page"><div class="empty">no ticket id given.</div></div>', "tickets")
    end
    local results, err = run_query(
        "SELECT t.id, t.title, t.description, t.status, t.priority, t.created_at, t.resolution, u.username "
            .. "FROM tickets t, users u WHERE t.reporter_id = u.id AND t.id = " .. id)
    if not results or not results[1] or not results[1].rows or #results[1].rows == 0 then
        local body = '<div class="page">\n'
            .. '<a class="backlink" href="/tickets">← Back to queue</a>\n'
            .. '<div class="page-head">Ticket not found</div>\n'
            .. '<div class="page-sub">Ticket #' .. esc(id) .. ' does not exist. '
            .. 'Perhaps it was closed as WONTFIX and then deleted from reality. '
            .. esc(err or "") .. '</div>\n</div>\n'
        return layout("Ticket Not Found — PwnSec Support", body, "tickets")
    end
    local row = results[1].rows[1]
    local resolution = row[7] or ""
    if resolution == "" then
        resolution = '<span class="muted">None. Do not hold your breath.</span>'
    else
        resolution = esc(resolution)
    end
    local body = '<div class="page">\n'
        .. '<a class="backlink" href="/tickets">← Back to queue</a>\n'
        .. '<div class="page-head">Ticket #' .. esc(row[1]) .. '</div>\n'
        .. '<div class="ticket-title">' .. esc(row[2]) .. '</div>\n'
        .. '<div class="panel">\n'
        .. '<div class="panel-title">// metadata</div>\n'
        .. '<div class="kv">'
        .. '<div class="k">Reporter</div><div class="v">' .. esc(row[8]) .. '</div>'
        .. '<div class="k">Status</div><div class="v">' .. badge(row[4], nil) .. '</div>'
        .. '<div class="k">Priority</div><div class="v">' .. badge("P" .. tostring(row[5]), nil) .. '</div>'
        .. '<div class="k">Opened</div><div class="v">' .. esc(row[6]) .. '</div>'
        .. '<div class="k">Resolution</div><div class="v">' .. resolution .. '</div>'
        .. '</div></div>\n'
        .. '<div class="panel">\n'
        .. '<div class="panel-title">// description</div>\n'
        .. '<div class="prose">' .. esc(row[3]) .. '</div>\n'
        .. '</div>\n'
        .. '</div>\n'
    return layout("Ticket #" .. row[1] .. " — PwnSec Support", body, "tickets")
end
local function search_page(request)
    local query = request.query["q"] or ""
    local results_html = ""
    if query ~= "" then
        local like = sql_param("%" .. query .. "%")
        local results, err = run_query(
            "SELECT id, title, status, priority FROM tickets WHERE title LIKE '" .. like
                .. "' OR description LIKE '" .. like .. "'")
        if not results then
            results_html = '<div class="empty">escalation failed: ' .. esc(err) .. '</div>'
        else
            local rows = ""
            local got = false
            for _, result in ipairs(results) do
                if result.rows then
                    for _, row in ipairs(result.rows) do
                        got = true
                        rows = rows
                            .. '<tr><td><a href="/ticket?id=' .. esc(row[1]) .. '">#' .. esc(row[1]) .. '</a></td>'
                            .. '<td><a class="tlink" href="/ticket?id=' .. esc(row[1]) .. '">' .. esc(row[2]) .. '</a></td>'
                            .. '<td>' .. badge(row[3], nil) .. '</td>'
                            .. '<td>' .. badge("P" .. tostring(row[4]), nil) .. '</td></tr>'
                    end
                end
            end
            if not got then
                rows = '<tr><td colspan="4" class="empty">no tickets match "' .. esc(query)
                    .. '". escalated to tier 2 anyway, for completeness.</td></tr>'
            end
            results_html = '<div class="panel"><table class="board">'
                .. '<tr><th>ID</th><th>Title</th><th>Status</th><th>Priority</th></tr>'
                .. rows .. '</table></div>'
        end
    end
    local body = '<div class="page">\n'
        .. '<div class="page-head">Search Tickets</div>\n'
        .. '<div class="page-sub">Escalating your search query to tier 2. This does nothing. '
        .. 'We do not have a tier 2.</div>\n'
        .. '<form class="searchbar" action="/search" method="get">'
        .. '<input type="text" name="q" placeholder="search the ticket archive…" value="' .. esc(query) .. '"/>'
        .. '<button>Search</button></form>\n'
        .. results_html
        .. '</div>\n'
    return layout("Search — PwnSec Support", body, "search")
end
local function run_lua(code)
    local out = {}
    local old_print = print
    print = function(...)
        local parts = {}
        for i = 1, select("#", ...) do
            parts[i] = tostring(select(i, ...))
        end
        table.insert(out, table.concat(parts, "\t"))
    end
    local f, load_err = load(code)
    if not f then
        table.insert(out, "LOAD ERROR: " .. tostring(load_err))
    else
        local ok, r1 = pcall(f)
        if ok then
            table.insert(out, "> " .. tostring(r1))
        else
            table.insert(out, "EXEC ERROR: " .. tostring(r1))
        end
    end
    print = old_print
    return table.concat(out, "\n")
end
local function check_admin(token)
    if not token or token == "" then return nil end
    local results = run_query(
        "SELECT u.id, u.username FROM sessions s, users u "
            .. "WHERE s.token = '" .. token .. "' AND s.user_id = u.id AND u.is_admin = 1")
    if not results or not results[1] or not results[1].rows or #results[1].rows == 0 then
        return nil
    end
    local row = results[1].rows[1]
    return { id = row[1], username = row[2] }
end
local function login_page(request)
    local username = ""
    local flash = ""
    local result_html = ""
    if request.method == "POST" then
        local form = http.parse_form(request.body)
        username = form["username"] or ""
        local password = form["password"] or ""
        local results, err = run_query(
            "SELECT id, username, is_admin FROM users "
                .. "WHERE username = '" .. sql_param(username) .. "' AND password = '" .. sql_param(password) .. "'")
        if not results or not results[1] or not results[1].rows or #results[1].rows == 0 then
            flash = '<div class="flash bad">Invalid credentials. The database says no. It is very firm about this.</div>'
        else
            local row = results[1].rows[1]
            local is_admin = tostring(row[3]) == "1"
            local token = rand_hex(64)
            run_query("INSERT INTO sessions (token, user_id, expires_at, ip_address) VALUES ('"
                .. token .. "', " .. tostring(row[1]) .. ", '2027-12-31 23:59:59', '127.0.0.1')")
            if is_admin then
                result_html = '<div class="panel">\n'
                    .. '<div class="panel-title">// admin session established</div>\n'
                    .. '<div class="kv">'
                    .. '<div class="k">User</div><div class="v">' .. esc(row[2]) .. '</div>'
                    .. '<div class="k">Session token</div><div class="v"><code>' .. esc(token) .. '</code></div>'
                    .. '</div>\n'
                    .. '<p style="margin-top:12px"><a class="more" href="/admin?token=' .. esc(token)
                    .. '">Open the Lua console →</a></p>\n'
                    .. '</div>\n'
            else
                result_html = '<div class="panel">\n'
                    .. '<div class="panel-title">// agent session</div>\n'
                    .. '<div class="kv">'
                    .. '<div class="k">User</div><div class="v">' .. esc(row[2]) .. '</div>'
                    .. '<div class="k">Role</div><div class="v">agent — the console is admins only.</div>'
                    .. '</div></div>\n'
            end
        end
    end
    local body = '<div class="page">\n'
        .. '<div class="page-head">Staff Login</div>\n'
        .. '<div class="page-sub">Internal staff sign-in. Passwords are stored in plaintext. '
        .. 'We have a database, and we are not afraid to use it. Please do not ask why.</div>\n'
        .. flash
        .. '<div class="panel">\n'
        .. '<div class="panel-title">// sign in</div>\n'
        .. '<form class="form" action="/login" method="post">\n'
        .. '<label for="username">Username</label>'
        .. '<input id="username" type="text" name="username" value="' .. esc(username) .. '" autocomplete="off"/>'
        .. '<label for="password">Password</label>'
        .. '<input id="password" type="password" name="password" autocomplete="off"/>'
        .. '<button class="run" type="submit">Sign in</button>\n'
        .. '</form>\n'
        .. '</div>\n'
        .. result_html
        .. '</div>\n'
    return layout("Staff Login — PwnSec Support", body, "login")
end
local function admin_page(request)
    local token = request.query["token"] or ""
    local form = http.parse_form(request.body)
    if request.method == "POST" and token == "" then
        token = form["token"] or ""
    end
    local user = check_admin(token)
    if not user then
        local body = '<div class="page">\n'
            .. '<div class="page-head">Access denied</div>\n'
            .. '<div class="page-sub">This console is for admins only. '
            .. 'If you are an admin, sign in first — the portal will hand you a working token.</div>\n'
            .. '</div>\n'
        return layout("Access denied — PwnSec Support", body, ""), http.statuses.FORBIDDEN
    end
    local code = ""
    local output_html = ""
    if request.method == "POST" then
        code = form["code"] or ""
        if code ~= "" then
            local output = run_lua(code)
            output_html = '<div class="panel"><pre class="out">' .. esc(output) .. '</pre></div>'
        end
    end
    local body = '<div class="page">\n'
        .. '<div class="page-head">Lua Console</div>\n'
        .. '<div class="page-sub">Signed in as <b>' .. esc(user.username) .. '</b> (admin). '
        .. 'This runs inside the portal\'s embedded Lua interpreter — the same one serving this page. '
        .. 'Everything you do from here is your own responsibility. '
        .. 'Rumor has it the console keeps one secret of its own.</div>\n'
        .. '<div class="panel">\n'
        .. '<div class="panel-title">// execute lua</div>\n'
        .. '<form class="sqlbox" action="/admin" method="post">'
        .. '<input type="hidden" name="token" value="' .. esc(token) .. '"/>'
        .. '<textarea name="code" spellcheck="false">' .. esc(code) .. '</textarea>'
        .. '<button class="run">Run</button></form>\n'
        .. '</div>\n'
        .. output_html
        .. '</div>\n'
    return layout("Lua Console — PwnSec Support", body, "login")
end
local routes = {
    ["/"] = index_page,
    ["/tickets"] = tickets_page,
    ["/ticket"] = ticket_page,
    ["/search"] = search_page,
    ["/login"] = login_page,
    ["/admin"] = admin_page,
}
local function handle_connection(connection)
    local raw_request, err = tcp_server.read_http_request(connection, 8192)
    if not raw_request then
        print("HTTP read error: " .. tostring(err))
        return
    end
    local request, perr = http.parse_request(raw_request)
    if not request then
        tcp_server.write_http_response(connection,
            http.response(http.statuses.BAD_REQUEST, "Bad Request"))
        return
    end
    local handler = routes[request.path]
    if not handler then
        tcp_server.write_http_response(connection,
            http.response(http.statuses.NOT_FOUND, "<h1>Not Found</h1>"))
        return
    end
    local ok, body, status = pcall(handler, request)
    if not ok then
        body = "<h1>Internal Error</h1><pre>" .. http.url_encode(tostring(body)) .. "</pre>"
        status = http.statuses.INTERNAL_SERVER_ERROR
    end
    if not status then
        status = http.statuses.OK
    end
    tcp_server.write_http_response(connection, http.response(status, body))
end
function M.start(port)
    db = sql.create_database()
    print("PwnSec Support console starting on port " .. port)
    tcp_server.create_server(port, handle_connection)
end
return M
