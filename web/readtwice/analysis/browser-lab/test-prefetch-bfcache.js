const http=require('http'),puppeteer=require('puppeteer');let finalized=false,used=false,seen=[];
const server=http.createServer((q,s)=>{let u=new URL(q.url,'http://127.0.0.1:8139');seen.push({url:q.url,purpose:q.headers['sec-purpose'],site:q.headers['sec-fetch-site'],used});
 if(u.pathname==='/start')s.end(`<script>
 if(!name){name='first';let c=open('/controller');setTimeout(()=>{c.blur();focus();location='/report';let s=document.createElement('script');s.type='speculationrules';s.text='{"prefetch":[{"source":"list","urls":["/report"]}]}';document.body.append(s)},200)}
 else setTimeout(()=>location='/report',200)
 </script>`);
 else if(u.pathname==='/controller')s.end(`<script>opener.focus();setTimeout(()=>opener.history.back(),1500)</script>`);
 else if(u.pathname==='/report'){if(q.headers['sec-purpose']&&!used){used=true;s.setHeader('cache-control','no-store');s.end('<title>PREFETCH_OK</title>')}else{finalized=true;s.statusCode=403;s.end('<title>NAV</title>')}}else s.end('x')});
(async()=>{await new Promise(r=>server.listen(8139,'127.0.0.1',r));let b=await puppeteer.launch({executablePath:process.env.CHROME_PATH,headless:'new'}),p=await b.newPage();await p.goto('http://127.0.0.1:8139/start');await new Promise(r=>setTimeout(r,3000));console.log({seen,url:p.url(),title:await p.title()});await b.close();server.close()})();
