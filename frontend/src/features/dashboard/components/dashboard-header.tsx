"use client";

import { useCompassPanel } from "@/components/compass-panel";
import { AIMark } from "@/components/ui/ai-mark";

function greeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}

export function DashboardHeader({ firstName }: { firstName: string }) {
  const compass = useCompassPanel();

  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-ink">
          {greeting()}, {firstName}.
        </h1>
        <p className="mt-1 text-sm text-ink/50">Here&apos;s what needs your attention today.</p>
      </div>
      {/* Opens the real global Compass panel. Hidden when Compass has
          nothing it can answer for this user here, rather than shown
          as a button that leads nowhere. */}
      {compass.canAsk && (
        <button
          type="button"
          onClick={compass.open}
          className="inline-flex items-center gap-2 self-start rounded-md border border-line bg-white px-4 py-2 text-sm font-medium text-ink transition-colors hover:border-ink/30"
        >
          <AIMark className="h-3.5 w-3.5 text-accent" />
          Ask Compass
          <kbd className="rounded border border-line px-1.5 py-0.5 text-[10px] text-ink/40">
            {compass.shortcutLabel}
          </kbd>
        </button>
      )}
    </div>
  );
}
