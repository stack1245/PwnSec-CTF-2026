const http = require('http');
const puppeteer = require('puppeteer');

const server = http.createServer((req, res) => {
  res.writeHead(200, {'content-type': 'text/html'});
  res.end(`<title>${req.url}</title>`);
});

(async () => {
  await new Promise(resolve => server.listen(8124, '127.0.0.1', resolve));
  const browser = await puppeteer.launch({executablePath: '../tools/chrome-152/chrome-win64/chrome.exe', headless: 'new'});
  for (const attr of ['id=viewer', 'name=viewer', 'id=viewer name=viewer']) {
    const page = await browser.newPage();
    await page.setContent(`<iframe ${attr} src=http://127.0.0.1:8124/initial></iframe>`);
    await new Promise(resolve => setTimeout(resolve, 200));
    await page.evaluate(() => open('http://127.0.0.1:8124/target', 'viewer'));
    await new Promise(resolve => setTimeout(resolve, 500));
    console.log(attr, 'pages', (await browser.pages()).length, 'frames', page.frames().map(frame => frame.url()));
    for (const extra of (await browser.pages()).slice(2)) await extra.close();
    await page.close();
  }
  await browser.close();
  server.close();
})();
