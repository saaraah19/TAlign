/**
 * A tiny fake backend for component tests.
 *
 * Components talk to the API through `fetch`, so instead of mocking each
 * hook we replace `fetch` once and describe the backend's answers by
 * route. That keeps the tests close to reality — the real hooks, the real
 * `apiFetch` wrapper, the real error handling all run — and lets a test
 * assert on what was actually sent ("nothing is sent until confirmed").
 */
import { vi } from "vitest";

export interface RecordedCall {
  method: string;
  /** Path without the /api/v1 prefix, e.g. "/jobs/123". */
  path: string;
  /** Query string including the leading "?", or "". */
  search: string;
  body: unknown;
}

/** Use to answer with a specific status, e.g. `new MockResponse({ detail: "no" }, 401)`. */
export class MockResponse {
  constructor(
    public body: unknown,
    public status = 200,
    public headers: Record<string, string> = {},
  ) {}
}

interface Route {
  method: string;
  matcher: string | RegExp;
  respond: unknown;
}

class ApiMock {
  calls: RecordedCall[] = [];
  private routes: Route[] = [];

  /**
   * Register an answer: a value (or MockResponse), or a function of the
   * request for answers that depend on it. Later registrations win, so a
   * test can override a default.
   */
  on(method: string, matcher: string | RegExp, respond: (call: RecordedCall) => unknown): this;
  on(method: string, matcher: string | RegExp, respond: unknown): this;
  on(method: string, matcher: string | RegExp, respond: unknown): this {
    this.routes.unshift({ method: method.toUpperCase(), matcher, respond });
    return this;
  }

  reset(): void {
    this.calls = [];
    this.routes = [];
    vi.stubGlobal("fetch", (input: RequestInfo | URL, init?: RequestInit) =>
      this.handle(input, init),
    );
  }

  /** Calls that changed something (anything but GET), minus the app's own session refresh. */
  get writes(): RecordedCall[] {
    return this.calls.filter((c) => c.method !== "GET" && c.path !== "/auth/refresh");
  }

  find(method: string, path: string | RegExp): RecordedCall | undefined {
    return this.calls.find(
      (c) =>
        c.method === method.toUpperCase() &&
        (typeof path === "string" ? c.path === path : path.test(c.path)),
    );
  }

  private async handle(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
    const url = new URL(typeof input === "string" ? input : input.toString());
    const method = (init?.method ?? "GET").toUpperCase();
    const path = url.pathname.replace(/^\/api\/v1/, "");
    const rawBody = init?.body;
    const body = typeof rawBody === "string" ? JSON.parse(rawBody) : rawBody;
    const call: RecordedCall = { method, path, search: url.search, body };
    this.calls.push(call);

    const route = this.routes.find(
      (r) =>
        r.method === method &&
        (typeof r.matcher === "string" ? r.matcher === path : r.matcher.test(path)),
    );
    if (!route) return respond(new MockResponse({ detail: `unmocked ${method} ${path}` }, 404));

    const result = typeof route.respond === "function" ? route.respond(call) : route.respond;
    return respond(result instanceof MockResponse ? result : new MockResponse(result));
  }
}

function respond(r: MockResponse): Response {
  if (r.status === 204) return new Response(null, { status: 204 });
  return new Response(JSON.stringify(r.body), {
    status: r.status,
    headers: { "content-type": "application/json", ...r.headers },
  });
}

export const apiMock = new ApiMock();
