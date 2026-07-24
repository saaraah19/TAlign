/**
 * Minimal fetch wrapper.
 *
 * Every frontend call to the backend goes through here rather than
 * scattering `fetch(process.env.NEXT_PUBLIC_API_URL + "...")` across
 * components.
 *
 * Two things this handles centrally:
 *   - Attaches the in-memory access token as an Authorization header,
 *     via a module-level getter set by AuthProvider (features/auth) —
 *     never read from localStorage, since the whole point of splitting
 *     access/refresh tokens is that the access token only lives in JS
 *     memory, gone on page reload.
 *   - `credentials: "include"` on every request so the httpOnly refresh
 *     cookie is sent automatically to same-site auth endpoints.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

let accessTokenGetter: () => string | null = () => null;

/** Called once by AuthProvider so apiFetch can read the current token without a React import here. */
export function setAccessTokenGetter(getter: () => string | null): void {
  accessTokenGetter = getter;
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

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const token = accessTokenGetter();

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init?.headers,
    },
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail ?? detail;
    } catch {
      // response wasn't JSON — fall back to statusText
    }
    throw new ApiError(response.status, detail);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

/**
 * For multipart/form-data uploads (resume files). Deliberately does NOT
 * set Content-Type — the browser sets the correct multipart boundary
 * automatically when the body is a FormData instance.
 */
export async function apiFetchFormData<T>(path: string, formData: FormData): Promise<T> {
  const token = accessTokenGetter();

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    credentials: "include",
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: formData,
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail ?? detail;
    } catch {
      // ignore
    }
    throw new ApiError(response.status, detail);
  }

  return response.json() as Promise<T>;
}
