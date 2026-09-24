import express from "express";
import rateLimit from "express-rate-limit";

import { admin, challenge, flag, reportable, visit } from "./conf.js";

if (!flag.validate(flag.value)) {
  console.error(`[bot] FLAG is missing or malformed: ${flag.value}`);
  process.exit(1);
}

if (!admin.username || !admin.password) {
  console.error("[bot] ADMIN_USERNAME / ADMIN_PASSWORD are required to sign in");
  process.exit(1);
}

const app = express();

app.set("view engine", "ejs");
app.set("trust proxy", 1);
app.disable("x-powered-by");

app.use(express.urlencoded({ extended: false, limit: "16kb" }));
app.use(express.json({ limit: "16kb" }));

const limiter = rateLimit({
  windowMs: 60_000,
  max: challenge.rateLimit,
  standardHeaders: true,
  legacyHeaders: false,
  message: "The archivist walks slowly. Try again in a minute.",
});

const desk = express.Router();

desk.get("/", (req, res) => {
  res.render("report", {
    name: challenge.name,
    appUrl: challenge.appUrl.origin,
    dwellSeconds: Math.round(challenge.dwellMs / 1000),
    rateLimit: challenge.rateLimit,
  });
});

desk.post("/", limiter, async (req, res) => {
  const url = reportable(req.body?.url);

  if (!url) {
    return res.status(400).render("report", {
      name: challenge.name,
      appUrl: challenge.appUrl.origin,
      dwellSeconds: Math.round(challenge.dwellMs / 1000),
      rateLimit: challenge.rateLimit,
      error: "Only http:// and https:// URLs are filed.",
      value: typeof req.body?.url === "string" ? req.body.url.slice(0, 512) : "",
    });
  }

  try {
    await visit(url.href);
    res.render("report", {
      name: challenge.name,
      appUrl: challenge.appUrl.origin,
      dwellSeconds: Math.round(challenge.dwellMs / 1000),
      rateLimit: challenge.rateLimit,
      notice: `Filed. The archivist looked at ${url.href} and moved on.`,
      value: url.href,
    });
  } catch (e) {
    console.error(`[bot] visit failed: ${e.message}`);
    res.status(502).render("report", {
      name: challenge.name,
      appUrl: challenge.appUrl.origin,
      dwellSeconds: Math.round(challenge.dwellMs / 1000),
      rateLimit: challenge.rateLimit,
      error: "The round could not be completed.",
      value: url.href,
    });
  }
});

app.use("/report", desk);

app.get("/healthz", (req, res) => res.type("text/plain").send("ok"));

app.use((req, res) => {
  res.status(404).type("text/plain").send("nothing at this address");
});

app.listen(challenge.port, "0.0.0.0", () => {
  console.log(`[bot] report desk on :${challenge.port} -> app ${challenge.appUrl.origin}`);
});
