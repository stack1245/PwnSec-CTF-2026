const http = require('http');
const puppeteer = require('puppeteer');

const payload = `<!doctype html><meta http-equiv="content-security-policy" content="default-src 'none'"><div><template shadowrootmode=open><noscript><a alt="</noscript></template><meta http-equiv=refresh content='0;url=http://127.0.0.1:8123/receiver'>">x</a></noscript></div>`;

const server = http.createServer((req, res) => {
  console.log('http:', req.url);
  if (req.url === '/note') {
    res.writeHead(200, {
      'content-type': 'text/html; charset=utf-8',
      'content-security-policy': "sandbox allow-scripts; base-uri 'none'",
    });
    res.end(payload);
  } else if (req.url === '/receiver') {
    res.writeHead(200, {'content-type': 'text/html; charset=utf-8'});
    res.end(`<script>onmessage=e=>{document.title='got';e.ports[0]?.postMessage('ready')}</script>`);
  } else {
    res.writeHead(404).end();
  }
});

(async () => {
  await new Promise(resolve => server.listen(8123, '127.0.0.1', resolve));
  const browser = await puppeteer.launch({
    executablePath: '../tools/chrome-152/chrome-win64/chrome.exe',
    headless: 'new',
    args: ['--no-sandbox'],
  });
  const page = await browser.newPage();
  page.on('console', message => console.log('console:', message.text()));
  await page.setContent(`<iframe id=f sandbox=allow-scripts src=http://127.0.0.1:8123/note></iframe><script>
    const f=document.querySelector('#f');
    f.addEventListener('load',()=>{
      console.log('parent load '+f.src);
      const c=new MessageChannel();
      c.port1.onmessage=e=>console.log('PORT '+e.data);
      f.contentWindow.postMessage('render','*',[c.port2]);
    },{once:true});
  </script>`);
  await new Promise(resolve => setTimeout(resolve, 3000));
  console.log('frames:', page.frames().map(frame => frame.url()));
  await browser.close();
  server.close();
})();
