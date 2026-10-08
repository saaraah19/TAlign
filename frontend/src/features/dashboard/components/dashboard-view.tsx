"use client";

import { useAuth } from "@/features/auth";
import { useDashboard } from "../hooks/use-dashboard";
import { ActivityFeed } from "./activity-feed";
import { AttentionNeeded } from "./attention-needed";
import { DailyBriefCard } from "./daily-brief-card";
import { DashboardHeader } from "./dashboard-header";
import { HiringFunnel } from "./hiring-funnel";
import { KpiRow } from "./kpi-row";

/**
 * The recruiter-facing Dashboard -- redesigned as a decision-making
 * workspace rather than a list of database records. Backed entirely by
 * GET /dashboard (see app/api/v1/dashboard.py); the Daily Brief is the
 * one part of this that's LLM-generated (cached once per day server-
 * side), everything else -- KPIs, the funnel, attention items, activity
 * -- is deterministic aggregation refetched on every load.
 */
export function DashboardView() {
  const { user } = useAuth();
  const { data, isLoading, error } = useDashboard();

  if (isLoading) return <p className="text-sm text-ink/50">Loading your dashboard…</p>;
  if (error || !data) {
    return <p className="text-sm text-red-600">Could not load the dashboard.</p>;
  }

  return (
    <div className="flex flex-col gap-6">
      <DashboardHeader firstName={user?.first_name ?? ""} />
      <KpiRow kpis={data.kpis} />
      <DailyBriefCard brief={data.brief} />
      <HiringFunnel stageCounts={data.kpis.stage_counts} />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <AttentionNeeded
          awaitingReview={data.awaiting_review}
          lowApplicantJobs={data.low_applicant_jobs}
          pendingDrafts={data.pending_drafts}
        />
        <ActivityFeed analyses={data.recent_analyses} workflowRuns={data.recent_workflow_runs} />
      </div>
    </div>
  );
}
