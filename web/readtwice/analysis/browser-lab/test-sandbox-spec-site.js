const http = require('node:http');
const puppeteer = require('puppeteer');

const seen = [];
const server = http.createServer((req, res) => {
  if (req.url === '/sandbox') {
    res.writeHead(200, {
      'content-type': 'text/html',
      'content-security-policy': "sandbox allow-scripts; base-uri 'none'",
    });
    res.end(`<script type=speculationrules>{"prefetch":[{"source":"list","urls":["/dest"]}]}<\/script><script>setTimeout(()=>location='/dest',500)<\/script>`);
    return;
  }
  seen.push({url: req.url, site: req.headers['sec-fetch-site'], dest: req.headers['sec-fetch-dest'], purpose: req.headers['sec-purpose']});
  res.writeHead(200, {'content-type': 'text/html', 'cache-control': 'no-store'});
  res.end('ok');
});

(async () => {
  await new Promise(resolve => server.listen(8155, 'localhost', resolve));
  const browser = await puppeteer.launch({executablePath: process.env.CHROME_PATH, headless: 'new'});
  const page = await browser.newPage();
  await page.goto('http://localhost:8155/sandbox');
  await new Promise(resolve => setTimeout(resolve, 1500));
  console.log(JSON.stringify({seen, url: page.url()}, null, 2));
  await browser.close();
  server.close();
})();
