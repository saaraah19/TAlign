// Drives the STATIC EXPORT (served by frontend/scripts/serve-export.mjs, which mimics Render's
// static hosting and API proxy) with a real browser, and checks the behaviours a static site
// could break: deep links to dynamic pages, client navigation, the sign-in cookie through the
// proxy, and real pages that a wildcard rule must not swallow.
//   node verify-static.mjs        (stack must be running on TALIGN_URL, default :3000)
import { spawn } from "node:child_process";
import http from "node:http";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { launch, newPage, go, login, sleep, settled, BASE, PASSWORD } from "./lib.mjs";

let failures = 0;
const check = (name, ok, extra = "") => { console.log(`${ok ? "PASS" : "FAIL"}  ${name}${extra ? "  — " + extra : ""}`); if (!ok) failures++; };
const text = (p) => p.evaluate(() => document.body.innerText);
// the first link under `prefix` that carries a record id (not the navigation link to the list)
const idLink = (p, prefix) => p.evaluate((pre) => {
  const a = [...document.querySelectorAll("a[href]")].find((x) => new RegExp("^" + pre + "[0-9a-f-]{36}").test(x.getAttribute("href")));
  return a ? a.getAttribute("href") : null;
}, prefix);

const b = await launch();
try {
  // anonymous visitor: a public dynamic page, reached by deep link
  const anon = await newPage(b);
  await go(anon, "/careers/");
  check("public job list loads through the /api proxy", (await text(anon)).includes("Open positions") && /Engineer|Manager|Analyst/.test(await text(anon)));
  await anon.waitForFunction(() => document.querySelector('a[href*="/careers/"][href$="/"]:not([href="/careers/"])'), { timeout: 30000 }).catch(() => {});
  const href = await idLink(anon, "/careers/");
  await go(anon, href);
  check(`deep link ${href} renders the right job`, (await text(anon)).includes("Required skills") || (await text(anon)).includes("Apply"), anon.url());

  // recruiter
  const p = await newPage(b);
  await login(p, "emma.martin@northwind-robotics.com");
  check("sign-in through the proxy lands on the dashboard", p.url().includes("/dashboard"), p.url());
  check("dashboard shows data", (await text(p)).includes("Open roles"));

  await go(p, "/pipeline/");
  await p.waitForFunction((re) => [...document.querySelectorAll("a[href]")].some((x) => new RegExp(re).test(x.getAttribute("href"))), { timeout: 30000 }, "^/pipeline/[0-9a-f-]{36}");
  const cardHref = await idLink(p, "/pipeline/");
  await p.click(`a[href="${cardHref}"]`);
  await p.waitForFunction(() => /^\/pipeline\/[0-9a-f-]{36}/.test(location.pathname), { timeout: 60000 });
  await settled(p, { settle: 1500 });
  check("clicking a candidate opens their workspace", (await text(p)).includes("Resume Intelligence"), p.url());

  const deep = p.url();
  await p.reload({ waitUntil: "domcontentloaded" });
  await settled(p, { settle: 2000 });
  check("RELOAD on a candidate URL keeps the session and the page (deep link + refresh cookie via proxy)", p.url() === deep && (await text(p)).includes("Resume Intelligence"), p.url());

  await go(p, "/jobs/new/");
  check("/jobs/new is the real page, not swallowed by the /jobs/* rule", (await text(p)).includes("New job"));

  const cookies = await p.cookies(BASE + "/api/v1/auth/refresh"); // the cookie is scoped to this path
  const refresh = cookies.find((c) => c.name.toLowerCase().includes("refresh"));
  check("refresh cookie is stored for the site's own address, httpOnly", !!refresh && refresh.httpOnly, refresh ? `${refresh.name} path=${refresh.path}` : "none");

  // sign out
  await go(p, "/dashboard/");
  const btn = await p.waitForSelector("::-p-text(Sign out)");
  await btn.click(); await sleep(1500);
  await go(p, "/dashboard/");
  await sleep(1500);
  check("after sign-out a protected page sends you to /login", p.url().includes("/login"), p.url());
} finally { await b.close(); }

// ---------------------------------------------------------------------------------------------
// Phase 2: a SLEEPING backend. A second copy of the static site (port 3001) is pointed at a
// forwarder (port 8002) that this script can switch off and on, standing in for a free-tier API
// that sleeps and then wakes.
// ---------------------------------------------------------------------------------------------
{
  const frontendDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../frontend");
  const REAL = { host: "127.0.0.1", port: 8000 };
  let forwarder = null;
  const awake = () => new Promise((resolve) => {
    forwarder = http.createServer((req, res) => {
      const up = http.request({ ...REAL, method: req.method, path: req.url, headers: { ...req.headers, host: "127.0.0.1:8000" } },
        (r) => { res.writeHead(r.statusCode, r.headers); r.pipe(res); });
      up.on("error", () => { res.writeHead(502); res.end(); });
      req.pipe(up);
    }).listen(8002, "127.0.0.1", resolve);
  });
  const asleep = () => new Promise((resolve) => { forwarder.closeAllConnections?.(); forwarder.close(resolve); forwarder = null; });

  const site = spawn("node", ["scripts/serve-export.mjs"], { cwd: frontendDir, env: { ...process.env, PORT: "3001", BACKEND_URL: "http://127.0.0.1:8002" }, stdio: "ignore" });
  await sleep(1500);
  await awake();
  const b2 = await launch();
  try {
    const p2 = await newPage(b2);
    const S = "http://localhost:3001";
    await p2.goto(S + "/login/", { waitUntil: "domcontentloaded" });
    await settled(p2);
    await p2.type("input[type=email]", "emma.martin@northwind-robotics.com");
    await p2.type("input[type=password]", PASSWORD);
    await p2.click("button[type=submit]");
    await p2.waitForFunction(() => location.pathname.startsWith("/dashboard"), { timeout: 60000 });
    await settled(p2, { settle: 1500 });
    check("phase 2: signed in while the API is awake", (await text(p2)).includes("Open roles"));

    await asleep(); // the API goes to sleep
    await p2.reload({ waitUntil: "domcontentloaded" });
    await p2.waitForFunction(() => document.body.innerText.includes("Waking up the server"), { timeout: 30000 }).catch(() => {});
    const overlay = (await text(p2)).includes("Waking up the server");
    check("a sleeping API shows the branded 'waking up' screen (not errors, not the login page)", overlay && !p2.url().includes("/login"), p2.url());
    if (process.env.SHOT) { const { shot } = await import("./lib.mjs"); await shot(p2, "28-waking-up"); }

    await sleep(4000);
    check("while it sleeps, the visitor is NOT treated as signed out", !p2.url().includes("/login"), p2.url());

    await awake(); // the API finishes waking
    await p2.waitForFunction(() => !document.body.innerText.includes("Waking up the server") && document.body.innerText.includes("Open roles"), { timeout: 60000 }).catch(() => {});
    const recovered = (await text(p2)).includes("Open roles") && !(await text(p2)).includes("Waking up the server");
    check("when the API wakes, the screen goes away and the dashboard loads by itself, still signed in", recovered && p2.url().includes("/dashboard"), p2.url());
  } finally {
    await b2.close();
    if (forwarder) await asleep();
    site.kill();
  }
}
console.log(failures ? `\n${failures} check(s) FAILED` : "\nall static-export checks passed");
process.exit(failures ? 1 : 0);
