const http = require("node:http");
const puppeteer = require("puppeteer");

const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const heads = {
  patchfor: `<script id=x>document.documentElement.dataset.ran='1'<\/script><template patchfor=x><meta http-equiv="content-security-policy" content="default-src 'none'"></template>`,
  for: `<?start name=x><script>document.documentElement.dataset.ran='1'<\/script><?end><template for=x><meta http-equiv="content-security-policy" content="default-src 'none'"></template>`,
};
const server = http.createServer((req, res) => {
  const kind = new URL(req.url, "http://127.0.0.1:4103").searchParams.get("kind");
  res.setHeader("Content-Type", "text/html");
  res.write(`<!doctype html><html><head>${heads[kind]}`);
  setTimeout(() => res.end(`</head><body><div></div></body></html>`), 100);
});

(async () => {
  await new Promise((resolve) => server.listen(4103, "127.0.0.1", resolve));
  for (const args of [[], ["--enable-blink-features=DocumentPatching"]]) {
    const browser = await puppeteer.launch({ executablePath: CHROME, headless: "new", args });
    for (const kind of Object.keys(heads)) {
      const page = await browser.newPage();
      await page.goto(`http://127.0.0.1:4103/?kind=${kind}`, { waitUntil: "domcontentloaded" });
      console.log(JSON.stringify({ args, kind, ran: await page.evaluate(() => document.documentElement.dataset.ran), head: await page.evaluate(() => document.head.innerHTML) }));
      await page.close();
    }
    await browser.close();
  }
  server.close();
})();
