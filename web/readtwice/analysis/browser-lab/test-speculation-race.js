const http = require('http');
const puppeteer = require('puppeteer');

async function run(order) {
  let finalized = false;
  const seen = [];
  const server = http.createServer((req, res) => {
    const u = new URL(req.url, 'http://127.0.0.1:8130');
    seen.push({url:req.url, purpose:req.headers['sec-purpose'], site:req.headers['sec-fetch-site'], finalized});
    if (u.pathname === '/start') {
      res.end(`<script>setTimeout(()=>{
        const spec=()=>{const s=document.createElement('script');s.type='speculationrules';s.textContent='{"prefetch":[{"source":"list","urls":["/report"]}]}';document.body.append(s)};
        ${order === 'location-first' ? `location='/report';spec();` : `spec();location='/report';`}
      },100)</script>`);
    } else if (u.pathname === '/report') {
      if (!req.headers['sec-purpose']) {
        finalized = true;
        res.writeHead(403, {'content-type':'text/html', 'cache-control':'no-store'}).end('<title>NAV</title>nav');
      } else if (finalized) {
        res.end('<title>PREFETCH_OK</title>ok');
      } else {
        res.writeHead(403).end('too early');
      }
    } else res.end('x');
  });
  await new Promise(resolve => server.listen(8130, '127.0.0.1', resolve));
  const browser = await puppeteer.launch({executablePath: process.env.CHROME_PATH, headless:'new'});
  const page = await browser.newPage();
  await page.goto(`http://127.0.0.1:8130/start?o=${order}`);
  await new Promise(resolve => setTimeout(resolve,1000));
  console.log(order, {url:page.url(), title:await page.title(), seen});
  await browser.close(); server.close();
}

(async()=>{await run('location-first'); await run('spec-first')})();
