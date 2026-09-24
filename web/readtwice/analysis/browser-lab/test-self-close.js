const http=require('node:http'),puppeteer=require('puppeteer');
const s=http.createServer((q,r)=>r.end(`<script>setTimeout(()=>{opener=self;close()},100)</script>`));
(async()=>{await new Promise(x=>s.listen(8159,'localhost',x));let b=await puppeteer.launch({executablePath:process.env.CHROME_PATH,headless:'new'}),p=await b.newPage();await p.goto('http://localhost:8159/');await new Promise(x=>setTimeout(x,500));console.log({closed:p.isClosed(),pages:(await b.pages()).map(x=>x.url())});await b.close();s.close()})();
