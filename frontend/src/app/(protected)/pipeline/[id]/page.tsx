"use client";

import { useParams } from "next/navigation";
import {
  AnalysisDetail,
  APPLICATION_IS_TERMINAL,
  useApplication,
} from "@/features/applications";
import { CandidateActivity } from "@/features/applications/components/workspace/candidate-activity";
import { CandidateHeader } from "@/features/applications/components/workspace/candidate-header";
import { StageActions } from "@/features/applications/components/workspace/stage-actions";
import { StageJourney } from "@/features/applications/components/workspace/stage-journey";
import { CommunicationPanel } from "@/features/communication";
import { ANALYSIS_SUGGESTIONS, CompassAsk } from "@/features/compass";
import { HireWorkflowPanel } from "@/features/employees";

/**
 * The candidate workspace. Main column = what you read and write
 * (the assessment, the emails); right rail = what you act with (stage,
 * Compass, workflow, activity). The rail scrolls on its own on large
 * screens so Compass stays in reach while you read a long analysis.
 */
export default function ApplicationDetailPage() {
  const params = useParams<{ id: string }>();
  const { data: application, isLoading, error } = useApplication(params.id);

  if (isLoading) {
    return (
      <main className="mx-auto max-w-content px-6 py-8 sm:px-8">
        <div className="h-16 w-80 animate-pulse rounded-lg bg-ink/[0.05]" />
        <div className="mt-8 h-64 animate-pulse rounded-lg bg-ink/[0.05]" />
      </main>
    );
  }
  if (error || !application) {
    return (
      <main className="mx-auto max-w-content px-6 py-8 text-sm text-red-600 sm:px-8">
        Could not load this application.
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-content px-6 py-8 sm:px-8">
      <CandidateHeader application={application} />

      <div className="mt-8 grid gap-8 lg:grid-cols-[minmax(0,1fr)_340px]">
        <div className="flex min-w-0 flex-col gap-10">
          <AnalysisDetail applicationId={application.id} />
          <CommunicationPanel
            applicationId={application.id}
            isTerminal={APPLICATION_IS_TERMINAL[application.status]}
          />
        </div>

        <aside className="flex flex-col gap-4 lg:sticky lg:top-24 lg:max-h-[calc(100vh-7rem)] lg:self-start lg:overflow-y-auto">
          <div className="rounded-lg border border-line bg-white p-5">
            <p className="mb-4 text-sm font-medium text-ink">Pipeline</p>
            <StageJourney status={application.status} />
            <div className="mt-5">
              <StageActions applicationId={application.id} status={application.status} />
            </div>
          </div>

          <CompassAsk applicationId={application.id} suggestions={ANALYSIS_SUGGESTIONS} />

          <HireWorkflowPanel
            applicationId={application.id}
            enabled={application.status === "hired"}
          />

          <CandidateActivity application={application} />
        </aside>
      </div>
    </main>
  );
}
