const http=require('http');const puppeteer=require('../../mouse in the house/analysis/browser-lab/node_modules/puppeteer-core');
const s=http.createServer((q,r)=>r.end(`<meta http-equiv="Set-Cookie" content="FLAG=meta; Path=/"><script>document.body.innerText=document.cookie</script>`)).listen(9160);
(async()=>{let b=await puppeteer.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});let p=await b.newPage();await p.goto('http://localhost:9160');console.log(await p.evaluate(()=>document.cookie));await b.close();s.close()})();
