import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, apiFetch, setSessionHandlers } from "./api-client";
import { getBackendState, resetBackendStatusForTests, timings } from "./backend-status";

type Handler = (url: string, init: RequestInit) => Response | Promise<Response>;

const json = (status: number, body: unknown = {}) =>
  new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });

/** Replaces fetch with a router keyed by "METHOD path"; records every call. */
function stubFetch(routes: Record<string, Handler | Handler[]>) {
  const calls: { key: string; init: RequestInit }[] = [];
  const queues = new Map<string, Handler[]>();
  for (const [key, h] of Object.entries(routes)) queues.set(key, Array.isArray(h) ? [...h] : [h]);
  const fn = vi.fn(async (input: string | URL | Request, init: RequestInit = {}) => {
    const url = String(input);
    const path = url.replace(/^https?:\/\/[^/]+(\/api\/v1)?/, "");
    const key = `${(init.method ?? "GET").toUpperCase()} ${path}`;
    calls.push({ key, init });
    const queue = queues.get(key);
    if (!queue) throw new Error(`unexpected request: ${key}`);
    const handler = (queue.length > 1 ? queue.shift() : queue[0]) as Handler;
    return handler(url, init);
  });
  vi.stubGlobal("fetch", fn);
  return { calls, count: (key: string) => calls.filter((c) => c.key === key).length };
}

const authHeader = (init: RequestInit) => (init.headers as Record<string, string>)?.Authorization;

describe("api client: expired access token", () => {
  let token: string | null;
  const onExpired = vi.fn();

  beforeEach(() => {
    token = "old";
    onExpired.mockReset();
    setSessionHandlers({ getToken: () => token, setToken: (t) => (token = t), onExpired });
    resetBackendStatusForTests();
  });
  afterEach(() => vi.unstubAllGlobals());

  it("renews the token once and retries the request", async () => {
    const net = stubFetch({
      "GET /jobs": [() => json(401, { detail: "expired" }), () => json(200, { ok: true })],
      "POST /auth/refresh": () => json(200, { access_token: "new" }),
    });

    await expect(apiFetch("/jobs")).resolves.toEqual({ ok: true });

    expect(token).toBe("new");
    expect(authHeader(net.calls[0]!.init)).toBe("Bearer old");
    expect(authHeader(net.calls[2]!.init)).toBe("Bearer new");
    expect(onExpired).not.toHaveBeenCalled();
  });

  it("shares ONE renewal between requests that fail at the same moment", async () => {
    const net = stubFetch({
      "GET /a": [() => json(401), () => json(200, { a: 1 })],
      "GET /b": [() => json(401), () => json(200, { b: 1 })],
      "POST /auth/refresh": async () => {
        await new Promise((r) => setTimeout(r, 20));
        return json(200, { access_token: "new" });
      },
    });

    const [a, b] = await Promise.all([apiFetch("/a"), apiFetch("/b")]);

    expect(a).toEqual({ a: 1 });
    expect(b).toEqual({ b: 1 });
    expect(net.count("POST /auth/refresh")).toBe(1);
  });

  it("ends the session when the renewal fails", async () => {
    stubFetch({
      "GET /jobs": () => json(401, { detail: "expired" }),
      "POST /auth/refresh": () => json(401, { detail: "no session" }),
    });

    await expect(apiFetch("/jobs")).rejects.toMatchObject({ status: 401 });
    expect(onExpired).toHaveBeenCalledTimes(1);
  });

  it("does not try to renew for a visitor who was never signed in", async () => {
    token = null;
    const net = stubFetch({ "GET /jobs": () => json(401, { detail: "not authenticated" }) });

    await expect(apiFetch("/jobs")).rejects.toMatchObject({ status: 401 });
    expect(net.count("POST /auth/refresh")).toBe(0);
  });

  it("does not treat a wrong password as an expired token", async () => {
    const net = stubFetch({ "POST /auth/login": () => json(401, { detail: "Invalid email or password." }) });

    await expect(apiFetch("/auth/login", { method: "POST", body: "{}" })).rejects.toThrow("Invalid email or password.");
    expect(net.count("POST /auth/refresh")).toBe(0);
    expect(onExpired).not.toHaveBeenCalled();
  });
});

describe("api client: sleeping server", () => {
  beforeEach(() => {
    setSessionHandlers({ getToken: () => "t", setToken: () => {}, onExpired: () => {} });
    resetBackendStatusForTests();
    timings.pollStartMs = 5;
    timings.pollMaxMs = 10;
  });
  afterEach(() => vi.unstubAllGlobals());

  it("waits for the server and repeats a GET that hit a gateway error", async () => {
    const net = stubFetch({
      "GET /jobs": [() => json(503), () => json(200, { jobs: [] })],
      "GET /health": () => json(200, { status: "ok" }),
    });

    await expect(apiFetch("/jobs")).resolves.toEqual({ jobs: [] });

    expect(net.count("GET /jobs")).toBe(2);
    expect(net.count("GET /health")).toBeGreaterThanOrEqual(1);
    expect(getBackendState()).toBe("up");
  });

  it("repeats a GET after a network error too", async () => {
    let first = true;
    const net = stubFetch({
      "GET /jobs": () => {
        if (first) {
          first = false;
          throw new TypeError("Failed to fetch");
        }
        return json(200, { ok: 1 });
      },
      "GET /health": () => json(200),
    });

    await expect(apiFetch("/jobs")).resolves.toEqual({ ok: 1 });
    expect(net.count("GET /jobs")).toBe(2);
  });

  it("NEVER repeats a write on its own: a repeated POST could be applied twice", async () => {
    const net = stubFetch({
      "POST /jobs": () => {
        throw new TypeError("Failed to fetch");
      },
      "GET /health": () => json(200),
    });

    const error = (await apiFetch("/jobs", { method: "POST", body: "{}" }).catch((e) => e)) as ApiError;

    expect(error).toBeInstanceOf(ApiError);
    expect(error.status).toBe(0);
    expect(net.count("POST /jobs")).toBe(1);
  });

  it("an ordinary server error is not mistaken for a sleeping server", async () => {
    const net = stubFetch({ "GET /jobs": () => json(500, { detail: "boom" }) });

    await expect(apiFetch("/jobs")).rejects.toMatchObject({ status: 500 });
    expect(net.count("GET /jobs")).toBe(1);
    expect(getBackendState()).not.toBe("waking");
  });
});
