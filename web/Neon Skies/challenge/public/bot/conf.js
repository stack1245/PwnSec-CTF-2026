import { chromium } from "playwright";

export const challenge = {
  name: "Neon Skies",
  appUrl: new URL(process.env.APP_URL || "http://neon_skies:3000"),
  port: Number(process.env.PORT || 3001),
  rateLimit: Number(process.env.RATE_LIMIT || 6),
  navTimeoutMs: Number(process.env.NAV_TIMEOUT_MS || 10_000),
  dwellMs: Number(process.env.DWELL_MS || 8_000),
};

export const chromePath = process.env.CHROME_PATH || "/usr/bin/google-chrome-stable";

export const admin = {
  username: process.env.ADMIN_USERNAME || "",
  password: process.env.ADMIN_PASSWORD || "",
};

export const flag = {
  value: process.env.FLAG || "",
  validate: (f) => typeof f === "string" && /^[A-Za-z0-9_-]+\{.+\}$/.test(f),
};

export function reportable(raw) {
  if (typeof raw !== "string" || raw.length === 0 || raw.length > 2048) return null;

  let url;
  try {
    url = new URL(raw);
  } catch {
    return null;
  }

  if (url.protocol !== "http:" && url.protocol !== "https:") return null;
  if (!url.hostname) return null;

  return url;
}

async function signIn(page) {
  await page.goto(new URL("/login", challenge.appUrl).href, {
    timeout: challenge.navTimeoutMs,
    waitUntil: "domcontentloaded",
  });

  await page.fill('input[name="username"]', admin.username);
  await page.fill('input[name="password"]', admin.password);

  await Promise.all([
    page
      .waitForURL(/\/admin$/, { timeout: challenge.navTimeoutMs })
      .catch((e) => console.error(`[bot] sign-in did not land on /admin: ${e.message}`)),
    page.click('button[type="submit"]'),
  ]);
}

export async function visit(url) {
  console.log(`[bot] start: ${url}`);

  const browser = await chromium.launch({
    executablePath: chromePath,
    headless: true,
    args: [
      "--no-sandbox",
      "--disable-dev-shm-usage",
      "--disable-gpu",
      "--js-flags=--jitless",
    ],
  });

  const context = await browser.newContext({ ignoreHTTPSErrors: true });

  try {
    await context.addCookies([
      { name: "FLAG", value: flag.value, url: challenge.appUrl.origin, httpOnly: true, sameSite: "Strict" },
    ]);

    const page = await context.newPage();
    page.setDefaultTimeout(challenge.navTimeoutMs);

    await signIn(page);

    await page
      .goto(url, { timeout: challenge.navTimeoutMs, waitUntil: "domcontentloaded" })
      .catch((e) => console.error(`[bot] navigation to ${url} failed: ${e.message}`));

    await page.waitForTimeout(challenge.dwellMs);
  } finally {
    await context.close();
    await browser.close();
  }

  console.log(`[bot] end: ${url}`);
}
