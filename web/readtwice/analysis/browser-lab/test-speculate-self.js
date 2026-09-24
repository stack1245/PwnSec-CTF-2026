const http = require('http');
const puppeteer = require('puppeteer');

const seen = [];
const server = http.createServer((req, res) => {
  seen.push({url:req.url, site:req.headers['sec-fetch-site'], purpose:req.headers['sec-purpose']});
  res.end(`<script>
    setTimeout(()=>{
      const s=document.createElement('script');s.type='speculationrules';
      s.textContent=JSON.stringify({prerender:[{source:'list',urls:[location.href+'#go'],eagerness:'immediate'}]});
      document.body.append(s)
    },100)
  </script>`);
});

(async () => {
  await new Promise(resolve => server.listen(8129, '127.0.0.1', resolve));
  const browser = await puppeteer.launch({executablePath: process.env.CHROME_PATH, headless: 'new'});
  const page = await browser.newPage();
  await page.goto('http://127.0.0.1:8129/start?x=1');
  await new Promise(resolve => setTimeout(resolve, 1500));
  console.log(seen);
  await browser.close(); server.close();
})();
