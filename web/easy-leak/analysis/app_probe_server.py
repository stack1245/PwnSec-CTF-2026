from __future__ import annotations

import html
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "challenge" / "web" / "index.php").read_text(encoding="utf-8")
TOKEN = "TOKEN_abcdef0123456789"
CSP = "script-src 'none'; default-src 'self'; base-uri 'none'; frame-src 'none'; object-src 'none'"


def validate(value: str) -> str:
    if len(value.encode()) > 1024:
        return "Too long"
    if re.search(r"[^\x20-\x7e\r\n]", value):
        return "Invalid characters"
    if re.search(r"http|data|\\|\*|\[|\]|&|%|@|//", value, re.I):
        return "Invalid keywords"
    return value


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlsplit(self.path)
        if parsed.path == "/quirks":
            css = parse_qs(parsed.query, keep_blank_values=True).get("css", [""])[-1]
            body = (
                f"<link rel=stylesheet href='/?content={html.escape(css, quote=True)}'>"
                "<input value=x>"
            ).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=UTF-8")
            self.send_header("Content-Security-Policy", CSP)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if parsed.path == "/favicon.ico":
            print(f"FAVICON {parsed.query}", flush=True)
            body = b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
            self.send_response(200)
            self.send_header("Content-Type", "image/gif")
            self.send_header("Cache-Control", "public, max-age=300")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if parsed.path.startswith("/hit"):
            print(f"HIT {parsed.path}", flush=True)
            self.send_response(204)
            self.end_headers()
            return

        content = parse_qs(parsed.query, keep_blank_values=True).get(
            "content", ["{{ your_input }}"]
        )[-1]
        body = f"""<!DOCTYPE html>
<html>
<body>
  <h1>Easy-leak 🫨</h1>
  <h3>Source</h3>
  <pre>{html.escape(SOURCE)}</pre>
  <h3>Content</h3>
  {validate(content)}
  <h3>Token</h3>
  {html.escape(TOKEN)}  <h3>Usage</h3>
  <a href=\"/?content=your_input\">/?content=your_input</a>
</body>
</html>
""".encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=UTF-8")
        self.send_header("Content-Security-Policy", CSP)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


ThreadingHTTPServer(("127.0.0.1", 8770), Handler).serve_forever()
