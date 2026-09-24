const http = require('http');
const puppeteer = require('puppeteer');
const seen = [];
const server = http.createServer((q, s) => {
  seen.push({url:q.url, site:q.headers['sec-fetch-site'], dest:q.headers['sec-fetch-dest'], referer:q.headers.referer});
  if (q.url === '/start') s.end(`<!doctype html><a id=a href="http://localhost:8140/target" rel=noreferrer>go</a><script>a.click()</script>`);
  else s.end('<title>target</title>');
});
(async()=>{await new Promise(r=>server.listen(8140,'0.0.0.0',r)); const b=await puppeteer.launch({executablePath:process.env.CHROME_PATH,headless:'new'}); const p=await b.newPage(); await p.goto('http://127.0.0.1:8140/start'); await new Promise(r=>setTimeout(r,500)); console.log(seen); await b.close(); server.close();})();
