/**
 * Renders a component inside the same providers the real app has —
 * router, route params, React Query, auth, toasts — with the network
 * answered by `apiMock`. The signed-in user is described, not mocked:
 * the real AuthProvider runs its real startup (refresh, then /auth/me).
 */
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, render } from "@testing-library/react";
import { vi } from "vitest";
import { AppRouterContext } from "next/dist/shared/lib/app-router-context.shared-runtime";
import type { AppRouterInstance } from "next/dist/shared/lib/app-router-context.shared-runtime";
import {
  PathnameContext,
  PathParamsContext,
} from "next/dist/shared/lib/hooks-client-context.shared-runtime";
import { useState, type ReactElement } from "react";
import { ToastProvider } from "@/components/ui/toast";
import { AuthProvider } from "@/features/auth";
import { apiMock, MockResponse } from "./api-mock";

export interface TestUser {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  roles: string[];
  account_type: "internal" | "candidate";
  company_id: string | null;
  status: string;
  created_at: string;
}

export function makeUser(
  account_type: TestUser["account_type"],
  roles: string[],
  overrides: Partial<TestUser> = {},
): TestUser {
  return {
    id: "user-1",
    email: "sam@example.com",
    first_name: "Sam",
    last_name: "Quinn",
    roles,
    account_type,
    company_id: account_type === "candidate" ? null : "company-1",
    status: "active",
    created_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

export const candidate = () => makeUser("candidate", ["candidate"]);
export const recruiter = () => makeUser("internal", ["recruiter"]);
export const admin = () => makeUser("internal", ["admin"]);
export const employee = () => makeUser("internal", ["employee"]);

export interface RenderOptions {
  /** The URL path the component believes it is on. */
  path?: string;
  /** Dynamic route params, e.g. { id: "job-1" }. */
  params?: Record<string, string>;
  /** Signed-in user, or null for a visitor. */
  user?: TestUser | null;
}

export function renderApp(ui: ReactElement, options: RenderOptions = {}) {
  const { path = "/", params = {}, user = null } = options;
  const controls: { setPath: (path: string) => void } = { setPath: () => {} };

  /** Holds the current path in state so a test can "navigate" mid-test. */
  function Shell({ children }: { children: ReactElement }) {
    const [currentPath, setCurrentPath] = useState(path);
    controls.setPath = setCurrentPath;
    return <PathnameContext.Provider value={currentPath}>{children}</PathnameContext.Provider>;
  }

  apiMock.on(
    "POST",
    "/auth/refresh",
    user ? { access_token: "token", token_type: "bearer", expires_in: 1800 } : new MockResponse({ detail: "no session" }, 401),
  );
  if (user) apiMock.on("GET", "/auth/me", user);

  const pushes: string[] = [];
  const router: AppRouterInstance = {
    push: vi.fn((href: string) => void pushes.push(href)),
    replace: vi.fn((href: string) => void pushes.push(`replace:${href}`)),
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
    prefetch: vi.fn(),
  };
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });

  const result = render(
    <AppRouterContext.Provider value={router}>
      <Shell>
        <PathParamsContext.Provider value={params}>
          <QueryClientProvider client={queryClient}>
            <AuthProvider>
              <ToastProvider>{ui}</ToastProvider>
            </AuthProvider>
          </QueryClientProvider>
        </PathParamsContext.Provider>
      </Shell>
    </AppRouterContext.Provider>,
  );

  /** Simulates the user navigating to another page. */
  const navigate = (to: string) => act(() => controls.setPath(to));

  return { ...result, router, pushes, queryClient, navigate };
}
