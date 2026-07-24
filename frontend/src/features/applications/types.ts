export type ApplicationStatus =
  | "applied"
  | "screening"
  | "interview"
  | "offer"
  | "hired"
  | "rejected";

// Mirrors backend ApplicationService._ALLOWED_TRANSITIONS exactly.
// REJECTED is reachable from any non-terminal state, so it's handled
// separately from the single "next stage" forward map.
export const APPLICATION_FORWARD_TRANSITIONS: Record<
  ApplicationStatus,
  ApplicationStatus | null
> = {
  applied: "screening",
  screening: "interview",
  interview: "offer",
  offer: "hired",
  hired: null,
  rejected: null,
};

export const APPLICATION_CAN_REJECT: Record<ApplicationStatus, boolean> = {
  applied: true,
  screening: true,
  interview: true,
  offer: true,
  hired: false,
  rejected: false,
};

export const APPLICATION_STATUS_LABELS: Record<ApplicationStatus, string> = {
  applied: "Applied",
  screening: "Screening",
  interview: "Interview",
  offer: "Offer",
  hired: "Hired",
  rejected: "Rejected",
};

export interface JobSummary {
  id: string;
  title: string;
  company_id: string;
}

export interface CandidateSummary {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
}

export interface ApplicationWithJob {
  id: string;
  candidate_id: string;
  job_id: string;
  company_id: string;
  status: ApplicationStatus;
  created_at: string;
  updated_at: string;
  job: JobSummary;
}

export interface ApplicationWithCandidate extends ApplicationWithJob {
  candidate: CandidateSummary;
}

export interface ApplicationListResponse {
  items: ApplicationWithJob[];
  total: number;
  page: number;
  page_size: number;
}

export interface PipelineListResponse {
  items: ApplicationWithCandidate[];
  total: number;
  page: number;
  page_size: number;
}

// --- Slice 4: Resume Intelligence ---

export type AnalysisProgressStatus =
  | "not_started"
  | "parsing"
  | "analyzing"
  | "complete"
  | "failed";

export const ANALYSIS_PROGRESS_LABELS: Record<AnalysisProgressStatus, string> = {
  not_started: "No resume attached yet",
  parsing: "Parsing resume…",
  analyzing: "Analyzing alignment…",
  complete: "Analysis complete",
  failed: "Analysis failed",
};

export interface SkillMatch {
  skill: string;
  match_state: "matched" | "not_matched" | "insufficient_evidence";
  evidence: string | null;
}

export interface ExperienceFit {
  candidate_relevant_years: number | null;
  meets_minimum: boolean | null;
  justification: string | null;
}

export interface ResumeAnalysis {
  id: string;
  application_id: string;
  parsed_resume_id: string;
  status: string;
  overall_score: number | null;
  required_skills_score_pct: number | null;
  preferred_skills_score_pct: number | null;
  experience_score_pct: number | null;
  scoring_algorithm_version: string | null;
  required_skills_result: SkillMatch[];
  preferred_skills_result: SkillMatch[];
  experience_fit: ExperienceFit | null;
  matched_skills: string[];
  missing_skills: string[];
  strengths: string[];
  potential_concerns: string[];
  explanation: string | null;
  llm_provider: string | null;
  llm_model: string | null;
  prompt_version: string | null;
  error_message: string | null;
  analyzed_at: string | null;
  created_at: string;
}
