const puppeteer = require("puppeteer");

(async () => {
  const browser = await puppeteer.launch({
    executablePath: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    headless: "new",
  });
  const page = await browser.newPage();
  page.on("console", message => console.log("console", message.text()));
  await page.goto("http://127.0.0.1:8000/health");
  await page.evaluate(() => {
    const child = open("http://127.0.0.1:3001/", "target");
    setTimeout(() => {
      try {
        child.location = "javascript:document.title='INJECT'";
      } catch (error) {
        console.log(String(error));
      }
    }, 800);
  });
  await new Promise(resolve => setTimeout(resolve, 2000));
  for (const candidate of await browser.pages()) {
    console.log(JSON.stringify({ url: candidate.url(), title: await candidate.title() }));
  }
  await browser.close();
})();
