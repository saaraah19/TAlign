"use client";

import { useDashboard } from "../hooks/use-dashboard";
import { AwaitingReviewSection } from "./awaiting-review-section";
import { DailyBriefCard } from "./daily-brief-card";
import { LowApplicantJobsSection } from "./low-applicant-jobs-section";
import { PendingDraftsSection } from "./pending-drafts-section";
import { RecentAnalysesSection } from "./recent-analyses-section";
import { RecentWorkflowRunsSection } from "./recent-workflow-runs-section";

/**
 * The recruiter-facing Dashboard -- "what deserves my attention today,"
 * per the locked scope, not a KPI grid. Backed entirely by
 * GET /dashboard (see app/api/v1/dashboard.py); the Daily Brief is the
 * one part of this that's LLM-generated (cached once per day server-
 * side), everything below it is deterministic aggregation refetched on
 * every load.
 */
export function DashboardView() {
  const { data, isLoading, error } = useDashboard();

  if (isLoading) return <p className="text-sm text-gray-500">Loading your dashboard…</p>;
  if (error || !data) {
    return <p className="text-sm text-red-600">Could not load the dashboard.</p>;
  }

  return (
    <div className="flex flex-col gap-8">
      <DailyBriefCard brief={data.brief} />

      <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
        <AwaitingReviewSection applications={data.awaiting_review} />
        <LowApplicantJobsSection jobs={data.low_applicant_jobs} />
        <RecentAnalysesSection analyses={data.recent_analyses} />
        <RecentWorkflowRunsSection runs={data.recent_workflow_runs} />
      </div>

      <PendingDraftsSection drafts={data.pending_drafts} />
    </div>
  );
}
