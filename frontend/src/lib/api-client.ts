/**
 * Minimal fetch wrapper.
 *
 * Every frontend call to the backend goes through here rather than
 * scattering `fetch(process.env.NEXT_PUBLIC_API_URL + "...")` across
 * components.
 *
 * What this handles centrally:
 *   - Attaches the in-memory access token as an Authorization header. The
 *     token only ever lives in JS memory (never localStorage), gone on page
 *     reload; AuthProvider registers how to read and replace it.
 *   - `credentials: "include"` on every request so the httpOnly refresh
 *     cookie is sent automatically to the auth endpoints.
 *   - An EXPIRED ACCESS TOKEN: a 401 on a normal request triggers one silent
 *     refresh (shared by all requests that fail at the same moment) and one
 *     retry. If the refresh fails the session is over and AuthProvider is told.
 *   - A SLEEPING SERVER: the hosting tier puts the API to sleep when idle. A
 *     network failure or a 502/503/504 marks the backend as "waking" (see
 *     backend-status.ts, which drives the "waking up" screen). Requests that
 *     are safe to repeat (GETs, and the session refresh) then wait for the
 *     server and retry once. Others (POST/PATCH/DELETE) are never repeated
 *     automatically, because a repeated write could be applied twice.
 */

import { reportBackendDown, waitForBackend } from "./backend-status";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

interface SessionHandlers {
  getToken: () => string | null;
  setToken: (token: string | null) => void;
  /** The session is over: the access token expired and could not be renewed. */
  onExpired: () => void;
}

let handlers: SessionHandlers = { getToken: () => null, setToken: () => {}, onExpired: () => {} };

/** Called by AuthProvider so apiFetch can read, replace and drop the token without a React import here. */
export function setSessionHandlers(next: Partial<SessionHandlers>): void {
  handlers = { ...handlers, ...next };
}

/** Kept for callers that only need to supply the token. */
export function setAccessTokenGetter(getter: () => string | null): void {
  handlers = { ...handlers, getToken: getter };
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

// Endpoints where a 401 means "wrong credentials" or "no session", not "token expired".
const NO_RENEWAL = new Set([
  "/auth/login",
  "/auth/logout",
  "/auth/refresh",
  "/auth/register/company",
  "/auth/register/candidate",
]);

const isGatewayStatus = (status: number) => status === 502 || status === 503 || status === 504;

type InitFactory = (token: string | null) => RequestInit;

/** One round trip. A sleeping server shows up as a network error or a gateway status. */
async function attempt(path: string, makeInit: InitFactory, token: string | null, repeatable: boolean): Promise<Response> {
  const url = `${API_BASE_URL}${path}`;
  const send = () => fetch(url, { ...makeInit(token), credentials: "include" });

  try {
    const response = await send();
    if (!isGatewayStatus(response.status)) return response;
    reportBackendDown();
    if (!repeatable) return response;
  } catch {
    reportBackendDown();
    if (!repeatable) throw new ApiError(0, "The server is not reachable right now.");
  }

  await waitForBackend();
  try {
    return await send();
  } catch {
    throw new ApiError(0, "The server is not reachable right now.");
  }
}

let refreshInFlight: Promise<string | null> | null = null;

/** Exchanges the refresh cookie for a new access token. Concurrent callers share one request. */
export function refreshAccessToken(): Promise<string | null> {
  refreshInFlight ??= (async () => {
    try {
      const response = await attempt("/auth/refresh", () => ({ method: "POST" }), null, true);
      if (!response.ok) return null;
      const body = (await response.json()) as { access_token: string };
      handlers.setToken(body.access_token);
      return body.access_token;
    } catch {
      return null;
    }
  })().finally(() => {
    refreshInFlight = null;
  });
  return refreshInFlight;
}

async function execute(path: string, makeInit: InitFactory): Promise<Response> {
  const method = (makeInit(null).method ?? "GET").toUpperCase();
  const repeatable = method === "GET" || path === "/auth/refresh";

  const usedToken = handlers.getToken();
  let response = await attempt(path, makeInit, usedToken, repeatable);

  if (response.status === 401 && usedToken && !NO_RENEWAL.has(path)) {
    const renewed = await refreshAccessToken();
    if (renewed) {
      response = await attempt(path, makeInit, renewed, repeatable);
    } else {
      handlers.onExpired();
    }
  }
  return response;
}

async function toApiError(response: Response): Promise<ApiError> {
  let detail = response.statusText;
  try {
    const body = await response.json();
    detail = body.detail ?? detail;
  } catch {
    // response wasn't JSON — fall back to statusText
  }
  return new ApiError(response.status, detail);
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await execute(path, (token) => ({
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init?.headers,
    },
  }));

  if (!response.ok) throw await toApiError(response);

  if (response.status === 204) {
    return undefined as T;
  }

  try {
    return (await response.json()) as T;
  } catch (err) {
    // A 2xx response with a body that isn't valid JSON (interrupted
    // connection, dev-server restart mid-response, proxy hiccup, etc.)
    // — the request may well have succeeded server-side even though we
    // can't read the response. Surface this as a real ApiError so
    // callers never see a bare, uninformative parse exception; see
    // useTransitionJob's onSettled for how the UI recovers from this.
    throw new ApiError(
      response.status,
      `Response could not be parsed (${err instanceof Error ? err.message : "unknown error"}).`,
    );
  }
}

/**
 * For multipart/form-data uploads (resume files). Deliberately does NOT
 * set Content-Type — the browser sets the correct multipart boundary
 * automatically when the body is a FormData instance.
 */
export async function apiFetchFormData<T>(path: string, formData: FormData): Promise<T> {
  const response = await execute(path, (token) => ({
    method: "POST",
    headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    body: formData,
  }));

  if (!response.ok) throw await toApiError(response);
  return response.json() as Promise<T>;
}
