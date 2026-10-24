import Link from "next/link";
import { AIMark } from "@/components/ui/ai-mark";
import type { DashboardBrief } from "../types";

/**
 * If `brief` is null, that means the LLM call failed this time (see
 * DashboardService's graceful-degradation design -- a failed Brief
 * generation never blocks the rest of the Dashboard). Render nothing
 * rather than an error banner; the other sections below still carry
 * the real information a recruiter needs.
 *
 * Deliberately the one dark, high-contrast surface on the Dashboard —
 * this is the single most distinctive component on the page, per the
 * redesign brief, and the only thing here that's actually
 * LLM-generated deserves to look different from the deterministic
 * data around it.
 */
export function DailyBriefCard({ brief }: { brief: DashboardBrief | null }) {
  if (!brief) return null;

  return (
    <div className="rounded-lg bg-ink p-6">
      <div className="flex items-center gap-2">
        <AIMark className="h-4 w-4 text-accent-light" />
        <p className="text-xs font-medium uppercase tracking-wide text-white/50">
          Your hiring brief
        </p>
      </div>
      <p className="mt-3 max-w-2xl text-[15px] leading-relaxed text-white/90">{brief.summary}</p>

      {brief.recommended_actions.length > 0 && (
        <div className="mt-5 flex flex-wrap gap-3">
          {brief.recommended_actions.map((action, i) =>
            action.application_id ? (
              <Link
                key={i}
                href={`/pipeline/${action.application_id}`}
                className="rounded-md bg-white px-3.5 py-2 text-sm font-medium text-ink transition-colors hover:bg-white/90"
              >
                {action.label}
              </Link>
            ) : (
              <span
                key={i}
                className="rounded-md border border-white/15 px-3.5 py-2 text-sm text-white/70"
              >
                {action.label}
              </span>
            )
          )}
        </div>
      )}
    </div>
  );
}
