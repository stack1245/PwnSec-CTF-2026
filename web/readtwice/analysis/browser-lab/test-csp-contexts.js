const puppeteer = require("puppeteer");
const CHROME = process.env.CHROME_PATH || "C:/Program Files/Google/Chrome/Application/chrome.exe";
const js = "top.__hits.push(NAME)";
const esc = (s) => s.replaceAll("&", "&amp;").replaceAll('"', "&quot;");
const variants = [
  ["iframe-js", `<iframe src="javascript:top.__hits.push('iframe-js')"></iframe>`],
  ["srcdoc-script", `<iframe srcdoc="${esc(`<script>top.__hits.push('srcdoc-script')<\/script>`)}"></iframe>`],
  ["srcdoc-iframe-js", `<iframe srcdoc="${esc(`<iframe src=&quot;javascript:top.__hits.push('srcdoc-iframe-js')&quot;></iframe>`)}"></iframe>`],
  ["srcdoc2-script", `<iframe srcdoc="${esc(`<iframe srcdoc=&quot;${esc(`<script>top.__hits.push('srcdoc2-script')<\/script>`)}&quot;></iframe>`)}"></iframe>`],
  ["object-js", `<object data="javascript:top.__hits.push('object-js')"></object>`],
  ["embed-js", `<embed src="javascript:top.__hits.push('embed-js')">`],
  ["svg-script", `<svg><script>top.__hits.push('svg-script')<\/script></svg>`],
  ["svg-href", `<svg><script href="data:text/javascript,top.__hits.push('svg-href')"></script></svg>`],
  ["img-error", `<img src=x onerror="top.__hits.push('img-error')">`],
  ["details", `<details open ontoggle="top.__hits.push('details')"></details>`],
  ["focus", `<input autofocus onfocus="top.__hits.push('focus')">`],
  ["svg-load", `<svg onload="top.__hits.push('svg-load')"></svg>`],
];
(async () => {
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: "new" });
  for (const [name, payload] of variants) {
    const page = await browser.newPage();
    await page.evaluateOnNewDocument(() => { window.__hits = []; });
    page.on("console", (m) => { if (m.type() === "error") console.log(name, m.text()); });
    await page.setContent(`<!doctype html><meta http-equiv="content-security-policy" content="default-src 'none'"><div><template shadowrootmode=open>${payload}</template></div>`);
    await new Promise((resolve) => setTimeout(resolve, 300));
    console.log(name, await page.evaluate(() => window.__hits));
    await page.close();
  }
  await browser.close();
})();
