from __future__ import annotations

import json
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parent
LOG = ROOT / "callback.jsonl"
GO = set()
VISITS = {}
APP = "http://localhost:3000"


class Handler(BaseHTTPRequestHandler):
    def _handle(self) -> None:
        record = {
            "time": datetime.now(timezone.utc).isoformat(),
            "method": self.command,
            "path": self.path,
            "headers": dict(self.headers),
        }
        with LOG.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")

        path = urlsplit(self.path).path
        query = urlsplit(self.path).query
        if path == "/" and "rid=" in query:
            VISITS[query] = VISITS.get(query, 0) + 1
            if VISITS[query] > 1:
                rid = dict(part.split("=", 1) for part in query.split("&") if "=" in part)["rid"]
                self.send_response(302)
                target = "http://localhost:3001" if "local=1" in query else APP
                self.send_header("Location", f"{target}/reports/check?rid={rid}")
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                return
        if path == "/helper":
            body = b"<!doctype html><script>setTimeout(()=>opener.history.back(),500)</script>"
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
            return
        if path == "/jump":
            rid = query.removeprefix("rid=")
            self.send_response(302)
            self.send_header("Location", f"http://localhost:3001/reports/check?rid={rid}")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            return
        candidate = ROOT / "callback.html"
        if path == "/health":
            body = b"ok"
            content_type = "text/plain; charset=utf-8"
        elif path == "/go":
            GO.add(query)
            body = b"ok"
            content_type = "text/plain; charset=utf-8"
        elif path == "/state":
            body = (b"go" if query in GO else b"wait")
            content_type = "text/plain; charset=utf-8"
        elif path == "/s.js":
            body = (ROOT / "s.js").read_bytes()
            content_type = "application/javascript; charset=utf-8"
        elif candidate.is_file():
            body = candidate.read_bytes()
            content_type = "text/html; charset=utf-8"
        else:
            body = b"<!doctype html><title>callback</title>"
            content_type = "text/html; charset=utf-8"

        self.send_response(200)
        if "go=" in self.headers.get("Cookie", ""):
            self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    do_GET = _handle
    do_HEAD = _handle


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
