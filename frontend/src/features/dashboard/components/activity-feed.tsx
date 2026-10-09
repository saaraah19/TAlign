import { AIMark } from "@/components/ui/ai-mark";
import { Card } from "@/components/ui/card";
import { formatRelativeTime } from "@/lib/format-relative-time";
import type { WorkflowRun } from "@/features/employees";
import type { RecentAnalysis } from "../types";

const WORKFLOW_NAME_LABELS: Record<string, string> = {
  hire_candidate: "Hiring workflow",
};

interface ActivityItem {
  key: string;
  timestamp: string;
  icon: "ai" | "check" | "cross";
  text: React.ReactNode;
}

/**
 * Merges two separately-fetched, separately-shaped lists (resume
 * analyses, workflow runs) into one human-readable, time-sorted feed —
 * per the redesign brief's "instead of raw hire_candidate strings, make
 * activity human-readable." No new data: both lists already come from
 * GET /dashboard, this only changes how they're presented.
 */
export function ActivityFeed({
  analyses,
  workflowRuns,
}: {
  analyses: RecentAnalysis[];
  workflowRuns: WorkflowRun[];
}) {
  const items: ActivityItem[] = [
    ...analyses
      .filter((a) => a.analyzed_at)
      .map(
        (a): ActivityItem => ({
          key: `analysis-${a.analysis_id}`,
          timestamp: a.analyzed_at as string,
          icon: "ai",
          text: (
            <>
              Compass completed resume analysis —{" "}
              <span className="font-medium text-ink">{a.candidate_name}</span> · {a.job_title}
            </>
          ),
        })
      ),
    ...workflowRuns.map(
      (run): ActivityItem => ({
        key: `run-${run.id}`,
        timestamp: run.created_at,
        icon: run.status === "failed" ? "cross" : "check",
        text: (
          <>
            {WORKFLOW_NAME_LABELS[run.workflow_name] ?? run.workflow_name}{" "}
            {run.status === "failed" ? "failed" : run.status === "skipped" ? "skipped" : "completed"}
          </>
        ),
      })
    ),
  ].sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

  return (
    <Card className="p-6">
      <h2 className="text-sm font-medium text-ink">Recent activity</h2>
      {items.length === 0 ? (
        <div className="mt-3">
          <p className="text-sm text-ink/60">No activity yet</p>
          <p className="mt-1 text-xs leading-relaxed text-ink/40">
            Applications, resume analyses and hires will show up here as they happen.
          </p>
        </div>
      ) : (
        <ul className="mt-4 flex flex-col gap-3.5">
          {items.slice(0, 8).map((item) => (
            <li key={item.key} className="flex items-start gap-2.5 text-sm">
              <span className="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center">
                {item.icon === "ai" && <AIMark className="h-3.5 w-3.5 text-accent" />}
                {item.icon === "check" && <span className="text-emerald-600">✓</span>}
                {item.icon === "cross" && <span className="text-red-500">✕</span>}
              </span>
              <span className="flex-1 text-ink/75">{item.text}</span>
              <span className="shrink-0 text-xs text-ink/35">
                {formatRelativeTime(item.timestamp)}
              </span>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
