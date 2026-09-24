const puppeteer = require("puppeteer");
const CHROME = process.env.CHROME_PATH || "C:/Program Files/Google/Chrome/Application/chrome.exe";
const metas = [
  `<meta http-equiv="content-security-policy" content="default-src 'none'" content="script-src 'unsafe-inline'">`,
  `<meta content="default-src 'none'" content="script-src 'unsafe-inline'" http-equiv="content-security-policy">`,
  `<meta http-equiv="content-security-policy" http-equiv="refresh" content="default-src 'none'">`,
  `<meta HTTP-EQUIV="content-security-policy" http-equiv="refresh" content="default-src 'none'">`,
];
(async () => {
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: "new" });
  for (const meta of metas) {
    const page = await browser.newPage();
    await page.setContent(`<!doctype html>${meta}<div><template shadowrootmode=open><script>document.title='ran'<\/script></template></div>`);
    console.log({ meta, title: await page.title(), head: await page.evaluate(() => document.head.innerHTML) });
    await page.close();
  }
  await browser.close();
})();
