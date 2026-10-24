// Shared helpers for capturing README screenshots. See README.md in this folder.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const here = path.dirname(fileURLToPath(import.meta.url));
export const OUT = path.resolve(here, "../../docs/assets/screenshots");
export const BASE = process.env.TALIGN_URL ?? "http://localhost:3000";
export const PASSWORD = "Demo!Pass123";
export const VIEW = { width: 1360, height: 860, deviceScaleFactor: 1 };

export async function launch() {
  const puppeteer = require("puppeteer-core");
  let executablePath = process.env.CHROME_PATH;
  let args = ["--no-sandbox"];
  if (!executablePath) {
    const chromium = (await import("@sparticuz/chromium")).default;
    executablePath = await chromium.executablePath();
    // --single-process (meant for serverless) breaks separate browser contexts, so drop it
    args = [...chromium.args.filter((a) => a !== "--single-process"), "--no-sandbox"];
  }
  return puppeteer.launch({ executablePath, args, headless: "shell", defaultViewport: VIEW });
}

// The app loads Inter from Google Fonts at build time. Where that is unreachable the app falls
// back to a system font, so Inter is injected from the @fontsource/inter package instead.
function fontCss() {
  const dir = path.dirname(require.resolve("@fontsource/inter/package.json")) + "/files";
  return [400, 500, 600, 700]
    .map((w) => {
      const b64 = fs.readFileSync(`${dir}/inter-latin-${w}-normal.woff2`).toString("base64");
      return `@font-face{font-family:'InterDemo';font-weight:${w};src:url(data:font/woff2;base64,${b64}) format('woff2');}`;
    })
    .join("") +
    "nextjs-portal,[data-nextjs-toast],[data-next-badge-root]{display:none !important;}body,body *:not(code):not(pre):not(.font-mono){font-family:'InterDemo',ui-sans-serif,system-ui,sans-serif !important;}";
}
const FONT = fontCss();

export async function newPage(browser) {
  const ctx = await browser.createBrowserContext(); // a separate "person": its own cookies
  const page = await ctx.newPage();
  await page.setViewport(VIEW);
  await page.evaluateOnNewDocument((css) => {
    document.addEventListener("DOMContentLoaded", () => {
      const s = document.createElement("style");
      s.textContent = css;
      document.head.appendChild(s);
    });
  }, FONT);
  return page;
}

export const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// Pages show grey "skeleton" placeholders while they fetch. Wait until none remain, rather than
// for network idleness (several screens poll the server and never go idle).
export async function settled(page, { settle = 700, timeout = 40000 } = {}) {
  const none = () => !document.querySelector(".animate-pulse");
  await page.waitForFunction(none, { timeout }).catch(() => {});
  await sleep(700); // a fetch may only start after first paint, so check a second time
  await page.waitForFunction(none, { timeout }).catch(() => {});
  await sleep(settle);
}

export async function go(page, urlPath, { settle = 700 } = {}) {
  await page.goto(BASE + urlPath, { waitUntil: "domcontentloaded", timeout: 120000 });
  await settled(page, { settle });
}

export async function login(page, email) {
  await go(page, "/login", { settle: 300 });
  await page.type("input[type=email]", email);
  await page.type("input[type=password]", PASSWORD);
  await Promise.all([
    page.waitForNavigation({ waitUntil: "domcontentloaded", timeout: 120000 }).catch(() => {}),
    page.click("button[type=submit]"),
  ]);
  await page
    .waitForFunction(() => location.pathname !== "/login", { timeout: 60000 })
    .catch(() => console.log("  !! still on /login after sign-in:", email));
  await settled(page, { settle: 1000 });
}

export async function clickText(page, text, { timeout = 15000 } = {}) {
  const el = await page.waitForSelector(`::-p-text(${text})`, { timeout });
  await el.click();
}

export async function shot(page, name, { fullPage = false, clip } = {}) {
  fs.mkdirSync(OUT, { recursive: true });
  const file = path.join(OUT, `${name}.png`);
  await page.screenshot({ path: file, fullPage, ...(clip ? { clip } : {}) });
  console.log("  saved", name, `(${Math.round(fs.statSync(file).size / 1024)} KB)`);
}

export async function scrollToText(page, text) {
  await page.evaluate((t) => {
    const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    let n;
    while ((n = w.nextNode())) {
      if (n.textContent.includes(t)) { n.parentElement.scrollIntoView({ block: "start" }); window.scrollBy(0, -90); return; }
    }
  }, text);
  await sleep(500);
}

// Click the button whose whole visible text equals `text` (clickText matches substrings, so
// "Approve" would also hit a filter chip called "Approved").
export async function clickExact(page, text) {
  await page.waitForFunction(
    (t) => [...document.querySelectorAll("button")].some((b) => b.innerText.trim() === t), { timeout: 15000 }, text);
  await page.evaluate((t) => [...document.querySelectorAll("button")].find((b) => b.innerText.trim() === t).click(), text);
}
