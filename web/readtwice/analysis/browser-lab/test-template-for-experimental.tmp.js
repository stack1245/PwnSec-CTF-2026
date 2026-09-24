const puppeteer = require("puppeteer");

const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const source = `<!doctype html><html><head><?start name=x><script>document.title='pwned'<\/script><?end><template for=x><meta http-equiv="content-security-policy" content="default-src 'none'"></template></head><body><div></div></body></html>`;

(async () => {
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: "new", args: ["--enable-experimental-web-platform-features"] });
  for (const enabled of [false, true]) {
    const page = await browser.newPage();
    await page.setJavaScriptEnabled(enabled);
    await page.setContent(source, { waitUntil: "domcontentloaded" });
    const result = await page.evaluate(() => {
      const declaration = document.head.firstElementChild;
      const surface = document.body.firstElementChild;
      const attributeProfile = [
        [document.documentElement, []], [document.head, []], [document.body, []],
        [declaration, ["http-equiv", "content"]], [surface, []],
      ].every(([element, allowed]) => element && element.getAttributeNames().every(name => allowed.includes(name)));
      return {
        title: document.title,
        head: document.head.innerHTML,
        body: document.body.innerHTML,
        nodes: [...document.head.childNodes].map(node => [node.nodeType, node.nodeName, node.textContent]),
        accepted: document.doctype?.name === "html"
          && document.head.childElementCount === 1
          && declaration?.localName === "meta"
          && declaration.httpEquiv.toLowerCase() === "content-security-policy"
          && declaration.content === "default-src 'none'"
          && document.body.childElementCount === 1
          && surface?.localName === "div"
          && surface.childElementCount === 0
          && document.body.textContent.trim() === ""
          && attributeProfile,
      };
    });
    console.log(JSON.stringify({ enabled, ...result }));
    await page.close();
  }
  await browser.close();
})();
