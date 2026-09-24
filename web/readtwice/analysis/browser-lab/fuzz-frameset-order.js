const puppeteer = require("puppeteer");

const CHROME = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const SCRIPT = `<script>top.__hit=1<\/script>`;
const META = `<meta http-equiv="content-security-policy" content="default-src 'none'">`;
const TOKENS = [
  "", "<html>", "</html>", "<head>", "</head>", "<body>", "</body>",
  "<frameset>", "</frameset>", "<frame>", "<noframes>", "</noframes>",
  "<template>", "</template>", "<table>", "</table>", "<tbody>", "</tbody>",
  "<tr>", "</tr>", "<select>", "</select>", "<form>", "</form>",
  "<svg>", "</svg>", "<math>", "</math>", "<p>", "</p>", "<div>", "</div>",
  "<noscript>", "</noscript>", "<!--x-->",
];

function rng(seed) {
  let state = seed >>> 0;
  return () => ((state = (state * 1664525 + 1013904223) >>> 0) / 2 ** 32);
}

(async () => {
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: "new" });
  const page = await browser.newPage();
  const candidates = [];
  const random = rng(0x4652414d);
  const endings = ["<div></div>", "<frameset><div></div></frameset>", "<body><div></div>", "<div>"];
  for (let i = 0; i < 24000; i++) {
    const prefix = Array.from({length: Math.floor(random() * 5)}, () => TOKENS[Math.floor(random() * TOKENS.length)]).join("");
    const middle = Array.from({length: 2 + Math.floor(random() * 9)}, () => TOKENS[Math.floor(random() * TOKENS.length)]).join("");
    const suffix = Array.from({length: Math.floor(random() * 6)}, () => TOKENS[Math.floor(random() * TOKENS.length)]).join("");
    candidates.push(`<!doctype html>${prefix}${SCRIPT}${middle}${META}${suffix}${endings[Math.floor(random() * endings.length)]}`);
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
      const profile = [
        [doc?.documentElement, []], [doc?.head, []], [doc?.body, []],
        [declaration, ["http-equiv", "content"]], [surface, []],
      ].every(([element, allowed]) => element && element.getAttributeNames().every(name => allowed.includes(name)));
      const ok = doc?.doctype?.name === "html" && doc.head.childElementCount === 1
        && declaration?.localName === "meta" && declaration.httpEquiv.toLowerCase() === "content-security-policy"
        && declaration.content === "default-src 'none'" && doc.body.childElementCount === 1
        && surface?.localName === "div" && surface.childElementCount === 0
        && doc.body.textContent.trim() === "" && profile;
      if (ok) accepted.push({source, html: doc.documentElement.outerHTML, bodyName: doc.body.localName});
      frame.remove();
    }
    return accepted;
  }, candidates);
  console.log(JSON.stringify({ tested: candidates.length, hits }, null, 2));
  await browser.close();
})();
