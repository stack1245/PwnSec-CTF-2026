local M = {}
function M.parse_request(data)
    local request = {
        method = nil,
        path = nil,
        query = {},
        headers = {},
        body = "",
        http_version = "1.1",
    }
    local header_part = data
    local body_part = ""
    local sep = data:find("\r\n\r\n")
    if sep then
        header_part = data:sub(1, sep - 1)
        body_part = data:sub(sep + 4)
    end
    local lines = {}
    for line in header_part:gmatch("[^\r\n]+") do
        table.insert(lines, line)
    end
    if #lines == 0 then
        return nil, "Empty request"
    end
    local request_line = lines[1]
    local method, full_path, http_version = request_line:match("^(%S+)%s+(%S+)%s+(.+)$")
    if not method then
        return nil, "Invalid request line: " .. request_line
    end
    request.method = method
    request.http_version = http_version
    local query_string = ""
    local path_part = full_path
    local qmark_pos = full_path:find("?")
    if qmark_pos then
        path_part = full_path:sub(1, qmark_pos - 1)
        query_string = full_path:sub(qmark_pos + 1)
    end
    request.path = M.url_decode(path_part)
    if query_string ~= "" then
        for pair in query_string:gmatch("[^&]+") do
            local key, value = pair:match("^([^=]*)=?(.*)$")
            if key then
                request.query[M.url_decode(key)] = M.url_decode(value)
            end
        end
    end
    for i = 2, #lines do
        local line = lines[i]
        local header_name, header_value = line:match("^([^:]+):%s*(.+)$")
        if header_name then
            request.headers[string.lower(header_name)] = header_value
        end
    end
    request.body = body_part
    return request
end
function M.url_decode(str)
    if not str then return "" end
    str = str:gsub("+", " ")
    str = str:gsub("%%(%x%x)", function(hex)
        return string.char(tonumber(hex, 16))
    end)
    return str
end
function M.url_encode(str)
    if not str then return "" end
    str = str:gsub("([^%w%.%-_])", function(c)
        return string.format("%%%02X", string.byte(c))
    end)
    return str
end
function M.parse_form(body)
    local form = {}
    if not body or body == "" then
        return form
    end
    for pair in body:gmatch("[^&]+") do
        local key, value = pair:match("^([^=]*)=?(.*)$")
        if key then
            form[M.url_decode(key)] = M.url_decode(value)
        end
    end
    return form
end
function M.format_response(status_code, status_text, body, headers)
    headers = headers or {}
    local response = "HTTP/1.1 " .. status_code .. " " .. status_text .. "\r\n"
    if not headers["Content-Type"] then
        headers["Content-Type"] = "text/html; charset=utf-8"
    end
    headers["Content-Length"] = tostring(#body)
    headers["Connection"] = "close"
    for key, value in pairs(headers) do
        response = response .. key .. ": " .. value .. "\r\n"
    end
    response = response .. "\r\n" .. body
    return response
end
M.statuses = {
    OK = {200, "OK"},
    BAD_REQUEST = {400, "Bad Request"},
    UNAUTHORIZED = {401, "Unauthorized"},
    FORBIDDEN = {403, "Forbidden"},
    NOT_FOUND = {404, "Not Found"},
    INTERNAL_SERVER_ERROR = {500, "Internal Server Error"},
}
function M.response(status, body, content_type)
    local status_code, status_text
    if type(status) == "table" then
        status_code, status_text = status[1], status[2]
    else
        status_code, status_text = status, "Unknown"
    end
    local headers = {}
    if content_type then
        headers["Content-Type"] = content_type
    end
    return M.format_response(status_code, status_text, body, headers)
end
return M
