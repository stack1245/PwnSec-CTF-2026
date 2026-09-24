const puppeteer = require("puppeteer");

(async () => {
  const browser = await puppeteer.launch({
    executablePath: "C:/Program Files/Google/Chrome/Application/chrome.exe",
    headless: true,
  });
  const base = `<!doctype html><meta http-equiv="content-security-policy" content="default-src 'none'"><div></div>`;
  for (const source of [`\ufeff${base}`, base]) {
    const page = await browser.newPage();
    await page.setJavaScriptEnabled(false);
    await page.setContent(source);
    console.log(await page.evaluate(() => ({
      doctype: document.doctype?.name,
      compatMode: document.compatMode,
      html: document.documentElement.outerHTML,
    })));
    await page.close();
  }
  await browser.close();
})();
