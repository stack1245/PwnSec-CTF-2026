const http=require('node:http'),puppeteer=require('puppeteer');
const seen=[];
const s=http.createServer((q,r)=>{seen.push(q.url);if(q.url==='/start'){r.setHeader('Content-Security-Policy','sandbox allow-scripts');r.end(`<script>document.title=navigator.userActivation.isActive;open('/popup')</script>`)}else r.end('popup')});
(async()=>{await new Promise(x=>s.listen(8156,'localhost',x));let b=await puppeteer.launch({executablePath:process.env.CHROME_PATH,headless:'new'}),p=await b.newPage();await p.goto('http://localhost:8156/start');await new Promise(x=>setTimeout(x,500));console.log({seen,title:await p.title(),pages:(await b.pages()).map(x=>x.url())});await b.close();s.close()})();
