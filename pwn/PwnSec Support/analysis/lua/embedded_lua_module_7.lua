local M = {}
function M.connect(ip_a, ip_b, ip_c, ip_d, port)
    local handle = tcp_connect(ip_a, ip_b, ip_c, ip_d, port)
    if handle >= 0 then
        return handle
    end
    return -1
end
function M.listen(port)
    local handle = tcp_listen(port)
    if handle >= 0 then
        return handle, port
    end
    return -1, handle
end
function M.accept(listen_handle)
    local handle = tcp_accept(listen_handle)
    if handle >= 0 then
        return handle, nil, nil
    end
    return -1, handle
end
function M.send(handle, data, length)
    if length ~= nil and length ~= #data then
        data = data:sub(1, length)
    end
    return tcp_send(handle, data)
end
function M.recv(handle, max_length)
    local data = tcp_recv(handle, max_length or 4096)
    if data ~= "" then
        return data, #data
    end
    return nil, 0
end
function M.close(handle)
    tcp_close(handle)
    return true
end
local Connection = {}
Connection.__index = Connection
function Connection:new(handle, peer_ip, peer_port)
    local obj = {
        handle = handle,
        peer_ip = peer_ip,
        peer_port = peer_port,
        closed = false,
    }
    setmetatable(obj, Connection)
    return obj
end
function Connection:send(data)
    if self.closed then return -1 end
    return M.send(self.handle, data)
end
function Connection:recv(max_length)
    if self.closed then return nil, -1 end
    max_length = max_length or 4096
    return M.recv(self.handle, max_length)
end
function Connection:close()
    if not self.closed then
        M.close(self.handle)
        self.closed = true
    end
end
local TCPServer = {}
TCPServer.__index = TCPServer
function TCPServer:new(port)
    local handle, actual_port = M.listen(port)
    if handle < 0 then
        return nil, actual_port
    end
    local obj = {
        handle = handle,
        port = actual_port,
    }
    setmetatable(obj, TCPServer)
    return obj
end
function TCPServer:accept()
    local handle, peer_ip, peer_port = M.accept(self.handle)
    if handle < 0 then
        return nil, peer_ip
    end
    return Connection:new(handle, peer_ip, peer_port)
end
function TCPServer:close()
    M.close(self.handle)
end
local TCPClient = {}
TCPClient.__index = TCPClient
function TCPClient:connect(ip_a, ip_b, ip_c, ip_d, port)
    local handle = M.connect(ip_a, ip_b, ip_c, ip_d, port)
    if handle < 0 then
        return nil, "connect failed"
    end
    local obj = {
        handle = handle,
        closed = false,
    }
    setmetatable(obj, TCPClient)
    return obj
end
function TCPClient:send(data)
    if self.closed then return -1 end
    return M.send(self.handle, data)
end
function TCPClient:recv(max_length)
    if self.closed then return nil, -1 end
    return M.recv(self.handle, max_length or 4096)
end
function TCPClient:close()
    if not self.closed then
        M.close(self.handle)
        self.closed = true
    end
end
M.Connection = Connection
M.TCPServer = TCPServer
M.TCPClient = TCPClient
return M
