/**
 * Tracks whether the API is awake.
 *
 * Why this exists: the product is hosted on a free tier that puts the API to sleep when nobody
 * has used it for a while, and waking it takes up to about a minute. The frontend is a static
 * site that never sleeps, so the visitor always gets the app instantly, and this module is what
 * lets the app notice "the server is still waking up" and say so, instead of showing errors or,
 * worse, treating a signed-in visitor as signed out because the first request failed.
 *
 * Three states:
 *   unknown : nothing has been learned yet (initial)
 *   up      : the last health check, or request, succeeded
 *   waking  : a request failed in the way a sleeping server fails (network error, or a gateway
 *             answering 502/503/504), and a health check is being repeated until it answers
 *
 * A 4xx or 500 from the API is NOT "waking": the server is awake and has answered.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export type BackendState = "unknown" | "up" | "waking";

/** Tunable so tests do not have to wait real seconds. */
export const timings = {
  probeTimeoutMs: 3000, // first check at start-up: slower than this means "probably asleep"
  pollTimeoutMs: 10_000, // one health check while waking
  pollStartMs: 1000,
  pollMaxMs: 4000,
  waiterGiveUpMs: 180_000, // a request waiting for the server stops waiting after this
};

let state: BackendState = "unknown";
let wakingSince: number | null = null;
let polling: Promise<void> | null = null;
const listeners = new Set<() => void>();

export const getBackendState = (): BackendState => state;
export const getWakingSince = (): number | null => wakingSince;

export function subscribeBackendState(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function setState(next: BackendState): void {
  if (next === state) return;
  state = next;
  wakingSince = next === "waking" ? Date.now() : null;
  listeners.forEach((l) => l());
}

const sleep = (ms: number) => new Promise<void>((r) => setTimeout(r, ms));

async function healthCheck(timeoutMs: number): Promise<boolean> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(`${API_BASE_URL}/health`, { cache: "no-store", signal: controller.signal });
    return response.ok;
  } catch {
    return false;
  } finally {
    clearTimeout(timer);
  }
}

async function pollUntilUp(): Promise<void> {
  let delay = timings.pollStartMs;
  for (;;) {
    if (await healthCheck(timings.pollTimeoutMs)) {
      setState("up");
      return;
    }
    await sleep(delay);
    delay = Math.min(delay * 1.5, timings.pollMaxMs);
  }
}

/** A request failed the way a sleeping server fails. Starts (once) the wait-until-awake loop. */
export function reportBackendDown(): void {
  if (state === "waking") return;
  setState("waking");
  polling = pollUntilUp().finally(() => {
    polling = null;
  });
}

/** Resolves when the server answers, or after a limit so a request never hangs forever. */
export function waitForBackend(): Promise<void> {
  if (state !== "waking" || !polling) return Promise.resolve();
  return Promise.race([polling, sleep(timings.waiterGiveUpMs)]);
}

/** Called once at start-up: is the server awake right now? */
export async function probeBackend(): Promise<void> {
  if (state === "waking") return;
  if (await healthCheck(timings.probeTimeoutMs)) setState("up");
  else reportBackendDown();
}

/** For tests only. */
export function resetBackendStatusForTests(): void {
  state = "unknown";
  wakingSince = null;
  polling = null;
  listeners.clear();
}
