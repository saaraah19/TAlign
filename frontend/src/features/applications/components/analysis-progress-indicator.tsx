"use client";

import { useMyAnalysisStatus } from "../hooks/use-applications";
import { ANALYSIS_PROGRESS_LABELS } from "../types";

const SPINNER_STATES = new Set(["parsing", "analyzing"]);

export function AnalysisProgressIndicator({ applicationId }: { applicationId: string }) {
  const { data, isLoading } = useMyAnalysisStatus(applicationId);

  if (isLoading || !data) return null;
  if (data.status === "not_started") return null;

  const isActive = SPINNER_STATES.has(data.status);
  const isFailed = data.status === "failed";
  const isComplete = data.status === "complete";

  return (
    <div className="flex items-center gap-2 rounded-md border border-gray-200 px-3 py-2 text-sm">
      {isActive && (
        <span className="h-3 w-3 animate-spin rounded-full border-2 border-gray-300 border-t-gray-900" />
      )}
      {isFailed && <span className="h-2 w-2 rounded-full bg-red-500" />}
      {isComplete && <span className="h-2 w-2 rounded-full bg-green-500" />}
      <span className={isFailed ? "text-red-600" : "text-gray-700"}>
        {ANALYSIS_PROGRESS_LABELS[data.status]}
      </span>
    </div>
  );
}
