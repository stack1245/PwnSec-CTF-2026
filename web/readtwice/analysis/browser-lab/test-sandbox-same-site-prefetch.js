const http = require('http');
const puppeteer = require('puppeteer');

(async () => {
  const seen = [];
  const server = http.createServer((req, res) => {
    seen.push({url:req.url, site:req.headers['sec-fetch-site'], dest:req.headers['sec-fetch-dest'], purpose:req.headers['sec-purpose'], cookie:req.headers.cookie});
    if (req.url === '/') res.end(`<iframe sandbox="allow-scripts" src="/child"></iframe>`);
    else if (req.url === '/child') res.end(`<script>setTimeout(()=>{let s=document.createElement('script');s.type='speculationrules';s.textContent='{"prefetch":[{"source":"list","urls":["/report"]}]}';document.body.append(s)},100)</script>`);
    else res.end('ok');
  });
  await new Promise(resolve => server.listen(8144, '127.0.0.1', resolve));
  const browser = await puppeteer.launch({executablePath:process.env.CHROME_PATH, headless:'new'});
  const page = await browser.newPage();
  page.on('request', req => console.log('event', req.url(), req.isNavigationRequest(), req.frame() === page.mainFrame()));
  await page.setCookie({name:'sid', value:'x', url:'http://127.0.0.1:8144', sameSite:'Lax'});
  await page.goto('http://127.0.0.1:8144/');
  await new Promise(resolve => setTimeout(resolve, 1500));
  console.log(seen);
  await browser.close();
  server.close();
})();
