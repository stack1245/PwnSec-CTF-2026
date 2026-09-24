const puppeteer = require("puppeteer");

const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const META = `<meta http-equiv="content-security-policy" content="default-src 'none'">`;
const PAYLOADS = [
  `<div><template shadowrootmode=open><script>top.__hit=1<\/script></template></div>`,
  `<div><template shadowrootmode=open><script>top.__hit=1<\/script></template>`,
  `<div><template shadowrootmode=open><script>top.__hit=1<\/script>`,
  `<div><template shadowrootmode=open><iframe srcdoc=x></iframe></template></div>`,
];
const TOKENS = [
  "", "<html>", "</html>", "<head>", "</head>", "<body>", "</body>",
  "<table>", "</table>", "<tbody>", "</tbody>", "<tr>", "</tr>",
  "<template>", "</template>", "<noscript>", "</noscript>",
  "<select>", "</select>", "<form>", "</form>", "<svg>", "</svg>",
  "<math>", "</math>", "<p>", "</p>", "<x>", "</x>", "<!--x-->",
];

function rng(seed) {
  let state = seed >>> 0;
  return () => ((state = (state * 1664525 + 1013904223) >>> 0) / 2 ** 32);
}

(async () => {
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: "new" });
  const page = await browser.newPage();
  const candidates = [];
  const random = rng(0x52454144);
  for (let i = 0; i < 12000; i++) {
    const before = Array.from({length: Math.floor(random() * 5)}, () => TOKENS[Math.floor(random() * TOKENS.length)]).join("");
    const middle = Array.from({length: Math.floor(random() * 6)}, () => TOKENS[Math.floor(random() * TOKENS.length)]).join("");
    const after = Array.from({length: Math.floor(random() * 5)}, () => TOKENS[Math.floor(random() * TOKENS.length)]).join("");
    candidates.push(`<!doctype html>${before}${PAYLOADS[Math.floor(random() * PAYLOADS.length)]}${middle}${META}${after}`);
  }
  const hits = await page.evaluate(async candidates => {
    const accepted = [];
    for (const source of candidates) {
      const frame = document.createElement("iframe");
      frame.sandbox = "";
      frame.hidden = true;
      document.body.append(frame);
      const loaded = new Promise(resolve => frame.onload = resolve);
      frame.srcdoc = source;
      await loaded;
      const doc = frame.contentDocument;
      const declaration = doc?.head?.firstElementChild;
      const surface = doc?.body?.firstElementChild;
      const attributeProfile = [
        [doc?.documentElement, []], [doc?.head, []], [doc?.body, []],
        [declaration, ["http-equiv", "content"]], [surface, []],
      ].every(([element, allowed]) => element && element.getAttributeNames().every(name => allowed.includes(name)));
      const ok = doc?.doctype?.name === "html"
        && doc.head.childElementCount === 1
        && declaration?.localName === "meta"
        && declaration.httpEquiv.toLowerCase() === "content-security-policy"
        && declaration.content === "default-src 'none'"
        && doc.body.childElementCount === 1
        && surface?.localName === "div"
        && surface.childElementCount === 0
        && doc.body.textContent.trim() === ""
        && attributeProfile;
      if (ok) accepted.push({source, html: doc.documentElement.outerHTML, shadow: surface.shadowRoot?.innerHTML});
      frame.remove();
    }
    return accepted;
  }, candidates);
  console.log(JSON.stringify({ tested: candidates.length, hits }, null, 2));
  await browser.close();
})();
