const http = require("node:http");
const puppeteer = require("puppeteer");
const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const source = `<!doctype html><html><head marker=x><?start name=x><script>document.documentElement.dataset.ran='1'<\/script><?end><template for=x><meta http-equiv="content-security-policy" content="default-src 'none'"></template></head><body><div></div></body></html>`;
const server = http.createServer((req, res) => res.end(source));
(async () => {
  await new Promise((resolve) => server.listen(4104, "127.0.0.1", resolve));
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: "new", args: ["--enable-blink-features=DocumentPatching"] });
  const page = await browser.newPage();
  await page.goto("http://127.0.0.1:4104", { waitUntil: "domcontentloaded" });
  console.log(await page.evaluate(() => ({ ran: document.documentElement.dataset.ran, html: document.documentElement.outerHTML })));
  await browser.close();
  server.close();
})();
