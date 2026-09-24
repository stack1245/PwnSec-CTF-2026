const http = require("node:http");
const puppeteer = require("puppeteer");

const CHROME = process.env.CHROME_PATH || "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const seen = [];
const visits = new Map();

const server = http.createServer((req, res) => {
  const url = new URL(req.url, "http://127.0.0.1:4100");
  if (url.pathname === "/dest") {
    seen.push({ method: url.searchParams.get("m"), site: req.headers["sec-fetch-site"], dest: req.headers["sec-fetch-dest"] });
    res.end("ok");
    return;
  }
  if (url.pathname === "/javascript-result") {
    seen.push({ method: "javascript-result", site: req.headers["sec-fetch-site"], dest: req.headers["sec-fetch-dest"] });
    res.end("ok");
    return;
  }
  const method = url.searchParams.get("m");
  const count = (visits.get(method) || 0) + 1;
  visits.set(method, count);
  if (method === "redirect") {
    res.writeHead(302, { Location: `/dest?m=${method}` }).end();
  } else if (method === "refresh-header") {
    res.writeHead(200, { "Content-Type": "text/html", Refresh: `0;url=/dest?m=${method}` }).end("wait");
  } else if (method === "meta") {
    res.end(`<meta http-equiv=refresh content="0;url=/dest?m=${method}">`);
  } else if (method === "js") {
    res.end(`<script>location='/dest?m=${method}'<\/script>`);
  } else if (method === "form") {
    res.end(`<form method=get action=/dest><input name=m value=${method}></form><script>document.forms[0].submit()<\/script>`);
  } else if (method === "reload") {
    seen.push({ method: `${method}-${count}`, site: req.headers["sec-fetch-site"], dest: req.headers["sec-fetch-dest"] });
    res.end(count === 1 ? `<script>location.reload()<\/script>` : "done");
  } else if (method === "history-go") {
    seen.push({ method: `${method}-${count}`, site: req.headers["sec-fetch-site"], dest: req.headers["sec-fetch-dest"] });
    res.end(count === 1 ? `<script>history.go(0)<\/script>` : "done");
  } else if (method === "reload-redirect") {
    seen.push({ method: `${method}-${count}`, site: req.headers["sec-fetch-site"], dest: req.headers["sec-fetch-dest"] });
    if (count === 1) res.end(`<script>location.reload()<\/script>`);
    else res.writeHead(302, { Location: `/dest?m=${method}` }).end();
  } else if (method === "prefetch") {
    res.end(`<link rel=prefetch href="/dest?m=${method}" as=document>`);
  } else if (method === "prerender") {
    res.end(`<link rel=prerender href="/dest?m=${method}">`);
  } else if (method === "speculation") {
    res.end(`<script type=speculationrules>{"prerender":[{"source":"list","urls":["/dest?m=${method}"]}]}<\/script>`);
  } else if (method === "speculation-activate") {
    res.end(`<script type=speculationrules>{"prerender":[{"source":"list","urls":["/dest?m=${method}"]}]}<\/script><script>setTimeout(()=>location='/dest?m=${method}',300)<\/script>`);
  } else if (method === "speculation-csp") {
    res.end(`<!doctype html><meta http-equiv="content-security-policy" content="default-src 'none'"><div><template shadowrootmode=open><script type=speculationrules>{"prerender":[{"source":"list","urls":["/dest?m=${method}"]}]}<\/script></template></div>`);
  } else if (method === "redirect-js") {
    res.writeHead(302, { Location: "javascript:location='/javascript-result'" }).end();
  } else if (method === "refresh-js") {
    res.writeHead(200, { "Content-Type": "text/html", Refresh: "0;url=javascript:location='/javascript-result'" }).end("wait");
  } else {
    res.end("bad");
  }
});

(async () => {
  await new Promise((resolve) => server.listen(4100, "127.0.0.1", resolve));
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: "new" });
  for (const method of ["redirect", "refresh-header", "meta", "js", "form", "reload", "history-go", "reload-redirect", "prefetch", "prerender", "speculation", "speculation-activate", "speculation-csp", "redirect-js", "refresh-js"]) {
    const page = await browser.newPage();
    page.on("request", (request) => {
      if (request.url().includes("/dest")) {
        seen.push({ method: `${method}-event`, navigation: request.isNavigationRequest(), main: request.frame() === page.mainFrame() });
      }
    });
    try {
      await page.goto(`http://127.0.0.1:4100/start?m=${method}`, { waitUntil: "domcontentloaded" });
    } catch (error) {
      seen.push({method: `${method}-error`, error: error.message});
    }
    await new Promise((resolve) => setTimeout(resolve, 500));
    await page.close();
  }
  console.log(JSON.stringify(seen, null, 2));
  await browser.close();
  server.close();
})();
