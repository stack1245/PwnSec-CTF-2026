const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({
    executablePath: '../tools/chrome-152/chrome-win64/chrome.exe',
    headless: 'new',
    args: ['--no-sandbox'],
  });
  const page = await browser.newPage();
  page.on('console', message => console.log('console:', message.text()));
  page.on('pageerror', error => console.log('pageerror:', error.message));
  page.on('request', request => console.log('request:', request.url()));
  await page.goto('http://127.0.0.1:8000/?local=1', {waitUntil: 'domcontentloaded'});
  await new Promise(resolve => setTimeout(resolve, 2000));
  await browser.close();
})();
