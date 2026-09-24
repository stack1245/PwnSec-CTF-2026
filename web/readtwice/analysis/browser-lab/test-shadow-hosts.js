const puppeteer = require("puppeteer");
const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
(async () => {
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: "new" });
  for (const host of ["html", "head", "body", "title", "meta", "div", "span", "p"]) {
    const page = await browser.newPage();
    const result = await page.evaluate((host) => {
      const el = document.createElement(host);
      try { el.attachShadow({ mode: "open" }); return true; } catch (e) { return e.name; }
    }, host);
    console.log(host, result);
    await page.close();
  }
  await browser.close();
})();
