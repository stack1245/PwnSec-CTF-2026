const http = require('http');
const puppeteer = require('puppeteer');

const seen = [];
const server = http.createServer((req, res) => {
  const url = new URL(req.url, 'http://127.0.0.1:8126');
  if (url.pathname === '/dest') {
    seen.push({m: url.searchParams.get('m'), site: req.headers['sec-fetch-site'], dest: req.headers['sec-fetch-dest']});
    res.end('ok');
    return;
  }
  const m = url.searchParams.get('m');
  const target = m === 'current' ? '_current' : m === 'self' ? '_self' : '';
  res.end(`<script>setTimeout(()=>open('/dest?m=${m}','${target}'),50)</script>`);
});

(async () => {
  await new Promise(resolve => server.listen(8126, '127.0.0.1', resolve));
  const browser = await puppeteer.launch({executablePath: process.env.CHROME_PATH, headless: 'new'});
  for (const m of ['current', 'self', 'blank-name']) {
    const page = await browser.newPage();
    await page.goto(`http://127.0.0.1:8126/start?m=${m}`);
    await new Promise(resolve => setTimeout(resolve, 500));
    await page.close();
  }
  console.log(seen);
  await browser.close();
  server.close();
})();
