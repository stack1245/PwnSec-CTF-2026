local tcp = require("tcp.tcp")
local M = {}
function M.create_server(port, handler)
    local server, err = tcp.TCPServer:new(port)
    if not server then
        error("Failed to create server: " .. tostring(err))
    end
    print("Server listening on port " .. server.port)
    while true do
        local connection, err = server:accept()
        if connection then
            local ok, result = pcall(handler, connection)
            if not ok then
                print("Error handling connection: " .. tostring(result))
            end
            connection:close()
        else
            print("Accept error: " .. tostring(err))
        end
    end
    server:close()
end
function M.read_http_request(connection, max_size)
    max_size = max_size or 8192
    local data = ""
    local attempts = 0
    while attempts < 100 do
        local chunk, err = connection:recv(max_size)
        if not chunk then
            return nil, "Connection closed or error: " .. tostring(err)
        end
        if chunk and #chunk > 0 then
            data = data .. chunk
        end
        attempts = attempts + 1
        local header_end = data:find("\r\n\r\n")
        if header_end then
            local headers = data:sub(1, header_end - 1)
            local body = data:sub(header_end + 4)
            local content_length = 0
            for line in headers:gmatch("[^\r\n]+") do
                local key, value = line:match("^([^:]+):%s*(.+)$")
                if key and string.lower(key) == "content-length" then
                    content_length = tonumber(value) or 0
                end
            end
            if #body >= content_length then
                return headers .. "\r\n\r\n" .. body:sub(1, content_length)
            end
        end
        wait(10)
    end
    return nil, "Timeout reading request"
end
function M.write_http_response(connection, response)
    local sent = 0
    local total = #response
    while sent < total do
        local chunk = response:sub(sent + 1, sent + 1024)
        local count = connection:send(chunk)
        if count <= 0 then
            return false, "Failed to send response"
        end
        sent = sent + count
    end
    return true
end
return M
