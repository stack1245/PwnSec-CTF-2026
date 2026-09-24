const http = require('http');
const puppeteer = require('puppeteer');

const server = http.createServer((req, res) => {
  res.writeHead(200, {'content-type': 'text/html'});
  if (req.url === '/child-open') res.end(`<script>open('/target','_current')</script>`);
  else if (req.url === '/child-form') res.end(`<form action=/target target=_current><button>go</button></form><script>document.forms[0].submit()</script>`);
  else res.end(`<title>${req.url}</title>`);
});

(async () => {
  await new Promise(resolve => server.listen(8125, '127.0.0.1', resolve));
  const browser = await puppeteer.launch({executablePath: process.env.CHROME_PATH, headless: 'new'});
  for (const method of ['open', 'form']) {
    const page = await browser.newPage();
    await page.setContent(`<title>parent</title><iframe sandbox="allow-scripts${method === 'form' ? ' allow-forms' : ''}" src=http://127.0.0.1:8125/child-${method}></iframe>`);
    await new Promise(resolve => setTimeout(resolve, 800));
    console.log(method, 'main=', page.url(), 'frames=', page.frames().map(frame => frame.url()), 'pages=', (await browser.pages()).map(p => p.url()));
    await page.close();
  }
  await browser.close();
  server.close();
})();
