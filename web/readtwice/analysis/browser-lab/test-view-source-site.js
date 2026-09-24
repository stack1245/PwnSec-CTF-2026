const http=require('node:http'),puppeteer=require('puppeteer');let seen=[];
const b=http.createServer((q,r)=>{seen.push({site:q.headers['sec-fetch-site'],dest:q.headers['sec-fetch-dest']});r.end('<b>target</b>')});
const a=http.createServer((q,r)=>r.end(`<script>location='view-source:http://localhost:${b.address().port}/target'</script>`));
(async()=>{await Promise.all([new Promise(x=>b.listen(0,'localhost',x)),new Promise(x=>a.listen(0,'127.0.0.1',x))]);let br=await puppeteer.launch({executablePath:process.env.CHROME_PATH,headless:'new'}),p=await br.newPage();p.on('console',x=>console.log(x.text()));await p.goto(`http://127.0.0.1:${a.address().port}/`);await new Promise(x=>setTimeout(x,800));console.log(seen,p.url());await br.close();a.close();b.close()})();
