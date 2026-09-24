const http=require('http'),puppeteer=require('puppeteer');let seen=[];
const a=http.createServer((q,s)=>s.end(`<iframe sandbox="allow-scripts allow-top-navigation" srcdoc="<script>top.location='http://127.0.0.1:8134/dest'<\/script>"></iframe>`));
const b=http.createServer((q,s)=>{seen.push({url:q.url,site:q.headers['sec-fetch-site'],dest:q.headers['sec-fetch-dest']});s.end('ok')});
(async()=>{await Promise.all([new Promise(r=>a.listen(8133,'127.0.0.1',r)),new Promise(r=>b.listen(8134,'127.0.0.1',r))]);let br=await puppeteer.launch({executablePath:process.env.CHROME_PATH,headless:'new'}),p=await br.newPage();await p.goto('http://127.0.0.1:8133/');await new Promise(r=>setTimeout(r,500));console.log(p.url(),seen);await br.close();a.close();b.close()})();
