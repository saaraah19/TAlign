import type { ApplicationWithCandidate } from "@/features/applications";
import type { WorkflowRun } from "@/features/employees";

export interface RecommendedAction {
  label: string;
  application_id: string | null;
}

export interface DashboardBrief {
  id: string;
  brief_date: string;
  summary: string;
  recommended_actions: RecommendedAction[];
  created_at: string;
}

export interface LowApplicantJob {
  job_id: string;
  title: string;
  applicant_count: number;
}

export interface RecentAnalysis {
  analysis_id: string;
  application_id: string;
  candidate_name: string;
  job_title: string;
  overall_score: number | null;
  analyzed_at: string | null;
}

export interface PendingDraftEmail {
  id: string;
  application_id: string;
  email_type: string;
  status: string;
  recipient_email: string;
  subject: string;
  created_at: string;
}

export interface DashboardData {
  brief: DashboardBrief | null;
  awaiting_review: ApplicationWithCandidate[];
  low_applicant_jobs: LowApplicantJob[];
  recent_analyses: RecentAnalysis[];
  recent_workflow_runs: WorkflowRun[];
  pending_drafts: PendingDraftEmail[];
}
