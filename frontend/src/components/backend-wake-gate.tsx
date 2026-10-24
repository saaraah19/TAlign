"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState, useSyncExternalStore } from "react";
import { AIMark } from "@/components/ui/ai-mark";
import {
  getBackendState,
  getWakingSince,
  probeBackend,
  subscribeBackendState,
} from "@/lib/backend-status";

/** A brief hiccup (one slow request) must not flash a full-screen message. */
const SHOW_AFTER_MS = 1200;
/** After this long, say plainly that it is taking longer than usual. */
const LONG_WAIT_SECONDS = 75;

/**
 * The "waking up the server" screen.
 *
 * The demo is hosted on a free tier that puts the API to sleep when idle; waking it takes up to
 * about a minute. The app itself is a static site and is always there instantly, so this is the
 * only waiting screen a visitor sees. It never replaces real errors: it appears only while the
 * server fails the way a sleeping server fails (see lib/backend-status.ts), and it goes away on
 * its own, refreshing whatever the page was trying to load.
 */
export function BackendWakeGate() {
  const queryClient = useQueryClient();
  const state = useSyncExternalStore(subscribeBackendState, getBackendState, () => "unknown" as const);
  const [visible, setVisible] = useState(false);
  const [seconds, setSeconds] = useState(0);
  const wasWaking = useRef(false);

  // Is the server awake right now? One check when the app starts.
  useEffect(() => {
    void probeBackend();
  }, []);

  // Show the screen only after a short grace period, and refetch everything once it is awake.
  useEffect(() => {
    if (state === "waking") {
      wasWaking.current = true;
      const timer = setTimeout(() => setVisible(true), SHOW_AFTER_MS);
      return () => clearTimeout(timer);
    }
    setVisible(false);
    if (state === "up" && wasWaking.current) {
      wasWaking.current = false;
      void queryClient.invalidateQueries();
    }
  }, [state, queryClient]);

  // Elapsed time, so the wait feels accounted for.
  useEffect(() => {
    if (!visible) return;
    const tick = () => setSeconds(Math.max(0, Math.round((Date.now() - (getWakingSince() ?? Date.now())) / 1000)));
    tick();
    const timer = setInterval(tick, 1000);
    return () => clearInterval(timer);
  }, [visible]);

  if (!visible) return null;

  return (
    <div
      role="status"
      aria-live="polite"
      className="fixed inset-0 z-[100] flex items-center justify-center bg-paper/95 px-6 backdrop-blur-sm"
    >
      <div className="w-full max-w-md rounded-2xl border border-line bg-white p-8 text-center shadow-sm">
        <div className="mx-auto flex h-11 w-11 items-center justify-center rounded-full bg-ink text-accent">
          <AIMark className="h-5 w-5" />
        </div>
        <h2 className="mt-5 text-lg font-semibold tracking-tight text-ink">Waking up the server…</h2>
        <p className="mt-2 text-sm leading-relaxed text-ink/60">
          Talign&rsquo;s demo runs on a free hosting plan that puts the server to sleep when nobody is
          using it. It usually wakes within a minute, and this page will continue on its own.
        </p>
        <div className="mt-6 h-1 overflow-hidden rounded-full bg-ink/[0.07]" aria-hidden="true">
          <div className="h-full w-1/3 animate-[wake-slide_1.6s_ease-in-out_infinite] rounded-full bg-ink/70" />
        </div>
        <p className="mt-3 text-xs text-ink/40">
          {seconds >= LONG_WAIT_SECONDS
            ? `Still starting after ${seconds}s. Free servers can occasionally take longer; you can keep this page open.`
            : `Waiting for ${seconds}s`}
        </p>
      </div>
    </div>
  );
}
