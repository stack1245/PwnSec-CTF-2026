const http = require("http");
const puppeteer = require(process.argv[2]);

const server = http.createServer((req, res) => {
  if (req.url === "/style.css") {
    res.setHeader("Content-Type", "text/css");
    res.end("body{background-image:url('/hit')}");
    return;
  }
  if (req.url === "/hit") {
    console.log("STYLESHEET_APPLIED");
    res.end();
    return;
  }
  if (req.url === "/admin") {
    res.end("<title>SECRET</title>");
    return;
  }

  if (req.url.startsWith("/status/")) {
    const status = Number(req.url.split("/").pop());
    res.writeHead(status, {
      "Content-Type": "text/html",
      Refresh: "0; url=javascript:document.title='PWNED-REFRESH'",
      Link: `<http://localhost:${server.address().port}/style.css>; rel=stylesheet`,
    });
    res.write("<script>document.title='PWNED-BODY'</script>");
    res.end();
    return;
  }

  res.writeHead(302, { Location: "javascript:document.title='PWNED'" });
  res.end();
});

server.listen(0, "127.0.0.1", async () => {
  const browser = await puppeteer.launch({
    executablePath: process.env.CHROME_PATH,
    headless: true,
    args: ["--no-sandbox"],
  });
  const page = await browser.newPage();
  await page.goto(`http://127.0.0.1:${server.address().port}/admin`);
  const results = [];
  for (const status of [204, 205, 304]) {
    await page.goto(`http://127.0.0.1:${server.address().port}/admin`);
    let error = "";
    try {
      await page.goto(`http://localhost:${server.address().port}/status/${status}`);
      await new Promise((resolve) => setTimeout(resolve, 100));
    } catch (exception) {
      error = exception.message;
    }
    results.push({ status, url: page.url(), title: await page.title(), error });
  }
  console.log(JSON.stringify(results));
  await browser.close();
  server.close();
});
