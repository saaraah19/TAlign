import Link from "next/link";
import type { DashboardBrief } from "../types";

/**
 * If `brief` is null, that means the LLM call failed this time (see
 * DashboardService's graceful-degradation design -- a failed Brief
 * generation never blocks the rest of the Dashboard). Render nothing
 * rather than an error banner; the other sections below still carry
 * the real information a recruiter needs.
 */
export function DailyBriefCard({ brief }: { brief: DashboardBrief | null }) {
  if (!brief) return null;

  return (
    <div className="rounded-lg border border-gray-200 bg-gray-50 p-5">
      <p className="text-xs font-medium uppercase tracking-wide text-gray-500">
        Daily alignment brief
      </p>
      <p className="mt-2 text-sm leading-relaxed text-gray-900">{brief.summary}</p>

      {brief.recommended_actions.length > 0 && (
        <ul className="mt-3 flex flex-col gap-1.5">
          {brief.recommended_actions.map((action, i) => (
            <li key={i} className="text-sm">
              {action.application_id ? (
                <Link
                  href={`/pipeline/${action.application_id}`}
                  className="font-medium text-gray-900 underline"
                >
                  {action.label}
                </Link>
              ) : (
                <span className="text-gray-700">{action.label}</span>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
