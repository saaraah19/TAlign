import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { resetBackendStatusForTests, timings } from "@/lib/backend-status";
import { BackendWakeGate } from "./backend-wake-gate";

function mount() {
  const client = new QueryClient();
  return render(
    <QueryClientProvider client={client}>
      <BackendWakeGate />
    </QueryClientProvider>,
  );
}

describe("BackendWakeGate", () => {
  let awake: boolean;

  beforeEach(() => {
    awake = false;
    resetBackendStatusForTests();
    timings.probeTimeoutMs = 100;
    timings.pollStartMs = 30;
    timings.pollMaxMs = 60;
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        if (!awake) throw new TypeError("Failed to fetch");
        return new Response("{}", { status: 200 });
      }),
    );
  });
  afterEach(() => vi.unstubAllGlobals());

  it("shows nothing when the server is already awake", async () => {
    awake = true;
    mount();
    await new Promise((r) => setTimeout(r, 400));
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });

  it("explains the wait while the server is asleep, then goes away by itself", async () => {
    mount();

    expect(await screen.findByText("Waking up the server…", {}, { timeout: 4000 })).toBeInTheDocument();
    expect(screen.getByRole("status")).toBeInTheDocument();

    awake = true; // the server finishes waking

    await waitFor(() => expect(screen.queryByRole("status")).not.toBeInTheDocument(), { timeout: 4000 });
  });
});
