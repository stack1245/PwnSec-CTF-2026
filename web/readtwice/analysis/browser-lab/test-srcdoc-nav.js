const http = require("node:http");
const puppeteer = require("puppeteer");

const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const seen = [];
const server = http.createServer((req, res) => {
  seen.push({ url: req.url, site: req.headers["sec-fetch-site"], dest: req.headers["sec-fetch-dest"] });
  if (req.url.startsWith("/landing")) {
    res.setHeader("Content-Type", "text/html");
    res.end(`<script>document.body.textContent='LANDED';parent.postMessage('landed','*')<\/script>`);
    return;
  }
  res.setHeader("Content-Type", "text/html");
  res.end("ok");
});

(async () => {
  await new Promise((resolve) => server.listen(4102, "127.0.0.1", resolve));
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: "new" });
  const variants = [
    ["plain", `<iframe srcdoc="<meta http-equiv=refresh content='0;url=http://127.0.0.1:4102/landing?plain'>"></iframe>`],
    ["sandbox", `<iframe sandbox=allow-scripts srcdoc="<meta http-equiv=refresh content='0;url=http://127.0.0.1:4102/landing?sandbox'>"></iframe>`],
    ["credentialless", `<iframe credentialless srcdoc="<meta http-equiv=refresh content='0;url=http://127.0.0.1:4102/landing?credentialless'>"></iframe>`],
  ];
  for (const [name, child] of variants) {
    const page = await browser.newPage();
    page.on("console", (m) => console.log(name, "console", m.text()));
    await page.setContent(`<!doctype html><meta http-equiv="content-security-policy" content="default-src 'none'">${child}`);
    await new Promise((resolve) => setTimeout(resolve, 800));
    console.log(name, await page.evaluate(() => [...document.querySelectorAll("iframe")].map((f) => ({ src: f.src, body: (() => { try { return f.contentDocument?.body?.innerText; } catch { return "ERR"; } })() }))));
    await page.close();
  }
  console.log(JSON.stringify(seen, null, 2));
  await browser.close();
  server.close();
})();
