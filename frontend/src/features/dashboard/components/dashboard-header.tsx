import Link from "next/link";
import { AIMark } from "@/components/ui/ai-mark";

function greeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}

export function DashboardHeader({ firstName }: { firstName: string }) {
  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-ink">
          {greeting()}, {firstName}.
        </h1>
        <p className="mt-1 text-sm text-ink/50">Here&apos;s what needs your attention today.</p>
      </div>
      {/* Links to the real Knowledge/Compass surface -- the global
          command panel (brief item 11) is a later phase, so this
          points at somewhere Compass genuinely already works rather
          than being a decorative button with nothing behind it. */}
      <Link
        href="/knowledge"
        className="inline-flex items-center gap-2 self-start rounded-md border border-line bg-white px-4 py-2 text-sm font-medium text-ink transition-colors hover:border-ink/30"
      >
        <AIMark className="h-3.5 w-3.5 text-accent" />
        Ask Compass
      </Link>
    </div>
  );
}
