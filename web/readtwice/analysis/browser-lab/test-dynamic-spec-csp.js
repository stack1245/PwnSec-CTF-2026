const http = require('http');
const puppeteer = require('puppeteer');

const seen=[];
const server=http.createServer((req,res)=>{
  seen.push(req.url);
  if(req.url==='/') res.end(`<!doctype html><?start name="x"><script>
    setTimeout(()=>document.head.innerHTML+='<script type=speculationrules>{"prefetch":[{"urls":["/hit"]}]}<\\/script>',100)
  </script><?end><template for="x"><meta http-equiv="content-security-policy" content="default-src 'none'"></template><div></div>`);
  else res.end('ok');
});
(async()=>{
  await new Promise(r=>server.listen(8131,'127.0.0.1',r));
  const b=await puppeteer.launch({executablePath:process.env.CHROME_PATH,headless:'new'});
  const p=await b.newPage(); p.on('console',m=>console.log(m.text()));
  await p.goto('http://127.0.0.1:8131/'); await new Promise(r=>setTimeout(r,1000));
  console.log(seen); await b.close(); server.close();
})();
