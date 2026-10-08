export type WorkflowRunStatus = "success" | "failed" | "skipped";

export const WORKFLOW_RUN_STATUS_LABELS: Record<WorkflowRunStatus, string> = {
  success: "Completed",
  failed: "Failed",
  skipped: "Already run",
};

export interface WorkflowRun {
  id: string;
  workflow_name: string;
  status: WorkflowRunStatus;
  completed_steps: string[];
  failed_step: string | null;
  error: string | null;
  created_at: string;
}

export interface OnboardingTask {
  id: string;
  title: string;
  completed: boolean;
}

export interface Employee {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  job_title: string;
  hire_date: string;
}

export interface HireWorkflowStatus {
  workflow_run: WorkflowRun | null;
  employee: Employee | null;
  onboarding_tasks: OnboardingTask[];
}

// Human-readable labels for the four hire-workflow steps, in order —
// mirrors app/workflow_engine/workflows/hire_candidate.py's step names
// exactly, so completed_steps/failed_step can render meaningfully.
// `grant_portal_access` was added alongside the candidate-to-employee
// account conversion work — this mapping had drifted out of sync with
// the backend's 4-step workflow until now (3 steps listed, backend had
// 4), caught while touching workflow-run display for the Dashboard
// redesign.
export const HIRE_WORKFLOW_STEP_LABELS: Record<string, string> = {
  create_employee_record: "Create employee record",
  create_onboarding_checklist: "Create onboarding checklist",
  draft_welcome_email: "Draft welcome email",
  grant_portal_access: "Grant portal access",
};

export const HIRE_WORKFLOW_STEP_ORDER = [
  "create_employee_record",
  "create_onboarding_checklist",
  "draft_welcome_email",
  "grant_portal_access",
];
