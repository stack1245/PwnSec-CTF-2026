import json
import socket
import ssl
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
endpoint = json.loads((ROOT / "instance.json").read_text(encoding="utf-8"))["endpoints"][0]

raw = bytearray()
with socket.create_connection((endpoint["host"], endpoint["port"]), timeout=10) as sock:
    context = ssl.create_default_context()
    with context.wrap_socket(sock, server_hostname=endpoint["host"]) as tls:
        while chunk := tls.recv(65536):
            raw.extend(chunk)

(ROOT / "analysis" / "remote-output.txt").write_bytes(raw)
print(f"captured {len(raw)} bytes")
