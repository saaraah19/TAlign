import { z } from "zod";

export type JobStatus = "draft" | "open" | "closed" | "archived";
export type EmploymentType = "full_time" | "part_time" | "contract" | "internship";

// Linear lifecycle, matches backend JobService._ALLOWED_TRANSITIONS
// exactly. Defined once here so every UI affordance (which button to
// show) reads from the same source instead of re-deriving the graph.
export const JOB_STATUS_TRANSITIONS: Record<JobStatus, JobStatus | null> = {
  draft: "open",
  open: "closed",
  closed: "archived",
  archived: null,
};

export const JOB_STATUS_LABELS: Record<JobStatus, string> = {
  draft: "Draft",
  open: "Open",
  closed: "Closed",
  archived: "Archived",
};

export const EMPLOYMENT_TYPE_LABELS: Record<EmploymentType, string> = {
  full_time: "Full-time",
  part_time: "Part-time",
  contract: "Contract",
  internship: "Internship",
};

export interface Job {
  id: string;
  company_id: string;
  created_by: string | null;
  title: string;
  description: string;
  employment_type: EmploymentType;
  location: string | null;
  salary_min: number | null;
  salary_max: number | null;
  status: JobStatus;
  // Recruiter-authored scoring criteria (Slice 4) — the OFFICIAL
  // checklist Resume Intelligence scores against. `description` above
  // is context only, never criteria.
  required_skills: string[];
  preferred_skills: string[];
  min_years_experience: number | null;
  created_at: string;
  updated_at: string;
}

export interface JobListResponse {
  items: Job[];
  total: number;
  page: number;
  page_size: number;
}

// Mirrors backend app/schemas/job.py validation, including the
// cross-field salary_min <= salary_max rule.
export const jobCreateSchema = z
  .object({
    title: z.string().min(2).max(255),
    description: z.string().min(1),
    employment_type: z.enum(["full_time", "part_time", "contract", "internship"]),
    location: z.string().max(255).optional().or(z.literal("")),
    salary_min: z.coerce.number().int().min(0).optional().or(z.literal("")),
    salary_max: z.coerce.number().int().min(0).optional().or(z.literal("")),
    // Comma-separated in the form UI, split into arrays before submit —
    // see JobCreateForm. These are the OFFICIAL scoring criteria; the
    // LLM never infers them from `description`.
    required_skills_text: z.string().optional().or(z.literal("")),
    preferred_skills_text: z.string().optional().or(z.literal("")),
    min_years_experience: z.coerce.number().int().min(0).optional().or(z.literal("")),
  })
  .refine(
    (data) =>
      !data.salary_min || !data.salary_max || Number(data.salary_min) <= Number(data.salary_max),
    { message: "Minimum salary cannot exceed maximum salary.", path: ["salary_max"] },
  );

export type JobCreateInput = z.infer<typeof jobCreateSchema>;
