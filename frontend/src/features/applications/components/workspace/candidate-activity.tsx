"use client";

import { EMAIL_TYPE_LABELS, useEmails } from "@/features/communication";
import { useHireWorkflowStatus, WORKFLOW_RUN_STATUS_LABELS } from "@/features/employees";
import { formatRelativeTime } from "@/lib/format-relative-time";
import { useAnalysis, useAnalysisStatus } from "../../hooks/use-applications";
import type { ApplicationWithCandidate } from "../../types";

interface ActivityEvent {
  key: string;
  at: string;
  text: string;
}

/**
 * A feed of things that actually happened to this application, each
 * with a real timestamp from the record it came from: the application
 * itself, the analysis, drafted/sent emails, the hire workflow. It
 * reads the same React Query caches the panels beside it already
 * fill, so it costs no extra requests.
 *
 * This is NOT a stage-by-stage history — see StageJourney's note.
 */
export function CandidateActivity({ application }: { application: ApplicationWithCandidate }) {
  const { data: status } = useAnalysisStatus(application.id);
  const { data: analysis } = useAnalysis(application.id, status?.status === "complete");
  const { data: emails } = useEmails(application.id);
  const { data: hire } = useHireWorkflowStatus(application.id, {
    enabled: application.status === "hired",
  });

  const events: ActivityEvent[] = [
    { key: "received", at: application.created_at, text: "Application received" },
  ];

  if (analysis?.analyzed_at) {
    events.push({
      key: "analysis",
      at: analysis.analyzed_at,
      text:
        analysis.overall_score !== null
          ? `Resume analyzed — alignment score ${Math.round(analysis.overall_score)}`
          : "Resume analyzed",
    });
  }

  for (const email of emails?.items ?? []) {
    const label = EMAIL_TYPE_LABELS[email.email_type];
    events.push({ key: `${email.id}-drafted`, at: email.created_at, text: `Drafted: ${label}` });
    if (email.sent_at) {
      events.push({
        key: `${email.id}-sent`,
        at: email.sent_at,
        text: `Marked as sent: ${label}`,
      });
    }
  }

  if (hire?.workflow_run) {
    events.push({
      key: "hire-workflow",
      at: hire.workflow_run.created_at,
      text: `Hire workflow — ${WORKFLOW_RUN_STATUS_LABELS[hire.workflow_run.status].toLowerCase()}`,
    });
  }

  events.sort((a, b) => new Date(b.at).getTime() - new Date(a.at).getTime());

  return (
    <div className="rounded-lg border border-line bg-white p-5">
      <p className="text-sm font-medium text-ink">Activity</p>
      <ul className="mt-3 flex flex-col gap-3">
        {events.map((event) => (
          <li key={event.key} className="flex items-start gap-2.5">
            <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-ink/25" />
            <div className="min-w-0">
              <p className="text-sm text-ink/80">{event.text}</p>
              <p className="text-xs text-ink/40" title={new Date(event.at).toLocaleString()}>
                {formatRelativeTime(event.at)}
              </p>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
