import socket
import ssl
import sys
import time

host = sys.argv[1]
payload = sys.stdin.read().rstrip("\r\n")
followup = sys.argv[2].replace("\\n", "\n") if len(sys.argv) > 2 else ""
for attempt in range(12):
    with socket.create_connection((host, 443), timeout=10) as raw:
        with ssl.create_default_context().wrap_socket(raw, server_hostname=host) as sock:
            sock.settimeout(3)
            try:
                banner = sock.recv(4096)
            except TimeoutError:
                banner = b""
            if b"~ " not in banner:
                time.sleep(2)
                continue
            sock.sendall(payload.encode("ascii") + b"\n")
            sock.settimeout(30)
            chunks = [banner]
            if followup:
                while b"# " not in b"".join(chunks):
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    chunks.append(chunk)
                sock.sendall(followup.encode("ascii"))
            while True:
                try:
                    chunk = sock.recv(4096)
                except TimeoutError:
                    break
                if not chunk:
                    break
                chunks.append(chunk)
            print(b"".join(chunks).decode("utf-8", errors="replace"), end="")
            break
