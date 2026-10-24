import { renderHook } from "@testing-library/react";
import {
  PathnameContext,
  PathParamsContext,
} from "next/dist/shared/lib/hooks-client-context.shared-runtime";
import type { ReactNode } from "react";
import { describe, expect, it } from "vitest";
import { STATIC_PLACEHOLDER_ID, useRouteId } from "./route-id";

function at(pathname: string, params: Record<string, string>) {
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <PathnameContext.Provider value={pathname}>
        <PathParamsContext.Provider value={params}>{children}</PathParamsContext.Provider>
      </PathnameContext.Provider>
    );
  };
}

describe("useRouteId", () => {
  it("uses the route param when Next supplies a real one", () => {
    const { result } = renderHook(() => useRouteId(), { wrapper: at("/pipeline/abc-123", { id: "abc-123" }) });
    expect(result.current).toBe("abc-123");
  });

  it("reads the id from the address bar when the page was built for the placeholder", () => {
    // The static export builds /pipeline/_ once; the real id is only in the URL.
    const { result } = renderHook(() => useRouteId(), {
      wrapper: at("/pipeline/63c420c8-8fc8-4782-ae0b-0be3c233dede/", { id: STATIC_PLACEHOLDER_ID }),
    });
    expect(result.current).toBe("63c420c8-8fc8-4782-ae0b-0be3c233dede");
  });

  it("finds the id on a nested route such as /careers/<id>/apply", () => {
    const { result } = renderHook(() => useRouteId(), {
      wrapper: at("/careers/job-9/apply/", { id: STATIC_PLACEHOLDER_ID }),
    });
    expect(result.current).toBe("job-9");
  });

  it("returns an empty string rather than the placeholder when there is no id in the URL", () => {
    const { result } = renderHook(() => useRouteId(), { wrapper: at("/pipeline", { id: STATIC_PLACEHOLDER_ID }) });
    expect(result.current).toBe("");
  });
});
