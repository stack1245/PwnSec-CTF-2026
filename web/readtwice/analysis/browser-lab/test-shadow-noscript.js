const puppeteer = require("puppeteer");
const CHROME = process.env.CHROME_PATH || "C:/Program Files/Google/Chrome/Application/chrome.exe";
const payloads = [
  `<noscript><a alt="</noscript><script>document.title='pwned'<\/script>">x</a></noscript>`,
  `<noscript><a alt="</noscript></template><script>document.title='pwned'<\/script>">x</a></noscript>`,
];
(async () => {
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: "new" });
  for (const payload of payloads) for (const enabled of [false, true]) {
    const page = await browser.newPage();
    await page.setJavaScriptEnabled(enabled);
    await page.setContent(`<!doctype html><meta http-equiv="content-security-policy" content="default-src 'none'"><div><template shadowrootmode=open>${payload}</template></div>`);
    console.log(JSON.stringify({ enabled, title: await page.title(), html: await page.evaluate(() => document.documentElement.outerHTML), shadow: await page.evaluate(() => document.body.firstElementChild.shadowRoot?.innerHTML) }));
    await page.close();
  }
  await browser.close();
})();
