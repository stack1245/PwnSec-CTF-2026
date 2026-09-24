const puppeteer = require("puppeteer");

const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const variants = [
  ["patchfor", `<script id=x>document.documentElement.dataset.ran='1'<\/script><template patchfor=x><meta http-equiv="content-security-policy" content="default-src 'none'"></template>`],
  ["for", `<script id=x>document.documentElement.dataset.ran='1'<\/script><template for=x><meta http-equiv="content-security-policy" content="default-src 'none'"></template>`],
];

(async () => {
  for (const extraArgs of [[], ["--enable-experimental-web-platform-features"]]) {
    const browser = await puppeteer.launch({ executablePath: CHROME, headless: "new", args: extraArgs });
    for (const [name, head] of variants) {
      for (const enabled of [false, true]) {
        const page = await browser.newPage();
        await page.setJavaScriptEnabled(enabled);
        await page.setContent(`<!doctype html><html><head>${head}</head><body><div></div></body></html>`, { waitUntil: "domcontentloaded" });
        console.log(JSON.stringify({ extraArgs, name, enabled, ran: await page.evaluate(() => document.documentElement.dataset.ran), head: await page.evaluate(() => document.head.innerHTML) }));
        await page.close();
      }
    }
    await browser.close();
  }
})();
