// Screenshot scenarios for the README. Run:  node scenarios.mjs <group> [<group>...]
// Groups: public candidate recruiter knowledge hire leave isolation failures
import { launch, newPage, go, login, shot, sleep, clickText, clickExact, scrollToText, settled } from "./lib.mjs";

const NW = (n) => `${n}@northwind-robotics.com`;
const CAND = (n) => `${n}@candidates-demo.com`;

async function step(label, fn) {
  try { await fn(); } catch (e) { console.log(`  !! ${label} failed: ${String(e.message).split("\n")[0]}`); }
}

async function ask(page, question, { waitFor } = {}) {
  const input = await page.waitForSelector('input[placeholder^="Ask"]', { visible: true, timeout: 15000 });
  await input.click({ clickCount: 3 });
  await input.type(question);
  await page.keyboard.press("Enter");
  await sleep(600);
  await page.waitForFunction(() => !document.body.innerText.includes("Compass is thinking"), { timeout: 60000 });
  if (waitFor) await page.waitForSelector(`::-p-text(${waitFor})`, { timeout: 30000 });
  await sleep(500);
}

async function openCandidate(page, name) {
  await go(page, "/pipeline");
  await clickText(page, name);
  await page.waitForFunction(() => /^\/pipeline\/[0-9a-f-]{36}/.test(location.pathname), { timeout: 60000 });
  await settled(page, { settle: 1200 });
}

const groups = {
  async public(b) {
    const p = await newPage(b);
    await go(p, "/"); await shot(p, "01-landing");
    await go(p, "/careers"); await shot(p, "02-careers");
    await step("job detail", async () => {
      await p.click('a[href^="/careers/"]'); await settled(p);
      await shot(p, "03-job-detail");
    });
  },

  async candidate(b) {
    const p = await newPage(b);
    await login(p, CAND("alex.johnson"));
    await go(p, "/applications"); await shot(p, "04-candidate-applications");
    await step("application detail", async () => {
      await p.waitForSelector('a[href^="/applications/"]', { timeout: 30000 });
      await p.click('a[href^="/applications/"]'); await settled(p);
      await ask(p, "What stage is my application at?").catch(() => {});
      await shot(p, "05-candidate-application", { fullPage: true });
    });
  },

  async apply(b) {
    const p = await newPage(b);
    await login(p, CAND("priya.nair"));
    await go(p, "/careers");
    await clickText(p, "Machine Learning Engineer");
    await p.waitForFunction(() => /^\/careers\/[0-9a-f-]{36}$/.test(location.pathname), { timeout: 60000 });
    await settled(p);
    await clickText(p, "Apply now");
    await p.waitForFunction(() => location.pathname.endsWith("/apply"), { timeout: 60000 }).catch(() => {});
    await settled(p, { settle: 1200 });
    await shot(p, "04a-apply");
  },

  async recruiter(b) {
    const p = await newPage(b);
    await login(p, NW("emma.martin"));
    await shot(p, "06-recruiter-dashboard", { fullPage: true });
    await go(p, "/pipeline"); await shot(p, "07-pipeline");
    await step("workspace", async () => {
      await openCandidate(p, "Alex Johnson");
      await shot(p, "08-workspace-assessment", { fullPage: true });
      await scrollToText(p, "Interview invitation");
      await shot(p, "09-workspace-communication");
    });
    await step("compass explain", async () => {
      await p.evaluate(() => window.scrollTo(0, 0)); await sleep(300);
      await clickText(p, "Why this score?");
      await p.waitForFunction(() => !document.body.innerText.includes("Compass is thinking"), { timeout: 60000 });
      await sleep(900);
      await p.evaluate(() => window.scrollTo(0, 430)); await sleep(500);
      await shot(p, "10-workspace-compass-explain");
    });
    await step("weak match", async () => {
      await openCandidate(p, "James O'Connor");
      await shot(p, "08b-workspace-weak-match", { fullPage: true });
    });
    await go(p, "/jobs"); await shot(p, "11-jobs");
    await go(p, "/jobs/new"); await shot(p, "12-job-new", { fullPage: true });
  },
};

groups.knowledge = async (b) => {
  const p = await newPage(b);
  await login(p, NW("emma.martin"));
  await go(p, "/knowledge"); await shot(p, "13-knowledge-library");
  await step("answer", async () => {
    await ask(p, "How many days of annual leave do I get?", { waitFor: "Leave Policy" });
    await shot(p, "14-knowledge-answer");
  });
  await step("no answer", async () => {
    await ask(p, "What is the dress code?");
    await p.evaluate(() => window.scrollBy(0, 250)); await sleep(400);
    await shot(p, "15-knowledge-no-answer");
  });
};

groups.hire = async (b) => {
  const e = await newPage(b);
  await login(e, NW("emma.martin"));
  await openCandidate(e, "Wei Zhang");
  await shot(e, "16-hire-offer-stage");
  await clickText(e, "Move to Hired");
  await sleep(9000);                       // the workflow runs in the background; the panel polls
  await e.evaluate(() => window.scrollTo(0, 0)); await sleep(800);
  await shot(e, "17-hire-workflow", { fullPage: true });
  const w = await newPage(b);              // the same person, now an employee
  await login(w, CAND("wei.zhang"));
  await shot(w, "18-employee-dashboard");
};

groups.leave = async (b) => {
  const s = await newPage(b);
  await login(s, CAND("sarah.lopez"));
  await go(s, "/portal/leave"); await shot(s, "19-employee-leave", { fullPage: true });
  const d = await newPage(b);
  await login(d, NW("david.chen"));
  await go(d, "/leave-requests"); await shot(d, "20-leave-approval");
  await step("approve", async () => {
    await clickExact(d, "Approve"); await sleep(1800);
    await shot(d, "21-leave-approved");
  });
  await go(s, "/portal/leave"); await shot(s, "22-employee-leave-after", { fullPage: true });
  await step("refused", async () => {
    await openCandidate(d, "Alex Johnson");
    await clickText(d, "Move to Offer"); await sleep(1500);
    await shot(d, "23-hiring-manager-refused");
  });
};

groups.isolation = async (b) => {
  const g = await newPage(b);
  await login(g, "grace.okafor@helix-health.io");
  await go(g, "/pipeline"); await shot(g, "24-helix-pipeline");
  await go(g, "/knowledge");
  await step("helix answer", async () => {
    await ask(g, "How many days of annual leave do I get?", { waitFor: "Leave Policy" });
    await shot(g, "25-helix-answer");
  });
  const n = await newPage(b);
  await login(n, "noah.fischer@brightpath-logistics.com");
  await shot(n, "26-brightpath-empty");
};

groups.failures = async (b) => {
  const h = await newPage(b);
  await login(h, CAND("hannah.schmidt"));
  await go(h, "/applications");
  await step("unreadable", async () => {
    await h.waitForSelector('a[href^="/applications/"]', { timeout: 30000 });
    await h.click('a[href^="/applications/"]');
    await h.waitForFunction(() => /^\/applications\/[0-9a-f-]{36}/.test(location.pathname), { timeout: 60000 });
    await settled(h, { settle: 1200 });
    await shot(h, "27-unreadable-resume", { fullPage: true });
  });
};

const wanted = process.argv.slice(2);
const browser = await launch();
try {
  for (const g of wanted) { console.log(`== ${g}`); await groups[g](browser); }
} finally { await browser.close(); }
