"use client";

import { useMyAnalysisStatus } from "../hooks/use-applications";
import { ANALYSIS_PROGRESS_LABELS } from "../types";

const SPINNER_STATES = new Set(["parsing", "analyzing"]);

/**
 * What the candidate sees of the automated review: only its progress,
 * never a score or any of the analysis itself (those are recruiter-only
 * by design). `aria-live` lets a screen reader announce each change as
 * the review moves along.
 */
export function AnalysisProgressIndicator({ applicationId }: { applicationId: string }) {
  const { data, isLoading } = useMyAnalysisStatus(applicationId);

  if (isLoading || !data) return null;
  if (data.status === "not_started") return null;

  const isActive = SPINNER_STATES.has(data.status);
  const isFailed = data.status === "failed";
  const isComplete = data.status === "complete";

  return (
    <div
      aria-live="polite"
      className="flex items-center gap-2.5 rounded-md border border-line bg-white px-3.5 py-2.5 text-sm"
    >
      {isActive && (
        <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-line border-t-ink" />
      )}
      {isFailed && <span className="h-2 w-2 rounded-full bg-red-500" />}
      {isComplete && <span className="h-2 w-2 rounded-full bg-emerald-500" />}
      <span className={isFailed ? "text-red-600" : "text-ink/70"}>
        {ANALYSIS_PROGRESS_LABELS[data.status]}
      </span>
    </div>
  );
}
