import { apiFetch } from "@/lib/api-client";
import type { Job, JobCreateInput, JobListResponse, JobStatus } from "./types";

function splitSkills(text?: string): string[] {
  if (!text) return [];
  return text
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
}

export const jobsApi = {
  list: (params?: { status?: JobStatus; page?: number; page_size?: number }) => {
    const query = new URLSearchParams();
    if (params?.status) query.set("status", params.status);
    if (params?.page) query.set("page", String(params.page));
    if (params?.page_size) query.set("page_size", String(params.page_size));
    const qs = query.toString();
    return apiFetch<JobListResponse>(`/jobs${qs ? `?${qs}` : ""}`);
  },

  get: (jobId: string) => apiFetch<Job>(`/jobs/${jobId}`),

  create: (input: JobCreateInput) =>
    apiFetch<Job>("/jobs", {
      method: "POST",
      body: JSON.stringify({
        title: input.title,
        description: input.description,
        employment_type: input.employment_type,
        location: input.location || null,
        salary_min: input.salary_min === "" ? null : Number(input.salary_min),
        salary_max: input.salary_max === "" ? null : Number(input.salary_max),
        required_skills: splitSkills(input.required_skills_text),
        preferred_skills: splitSkills(input.preferred_skills_text),
        min_years_experience:
          input.min_years_experience === "" || input.min_years_experience === undefined
            ? null
            : Number(input.min_years_experience),
      }),
    }),

  update: (jobId: string, input: Partial<JobCreateInput>) =>
    apiFetch<Job>(`/jobs/${jobId}`, { method: "PATCH", body: JSON.stringify(input) }),

  transition: (jobId: string, targetStatus: JobStatus) =>
    apiFetch<Job>(`/jobs/${jobId}/transition`, {
      method: "POST",
      body: JSON.stringify({ target_status: targetStatus }),
    }),

  remove: (jobId: string) => apiFetch<void>(`/jobs/${jobId}`, { method: "DELETE" }),
};

// Public, unauthenticated browsing — hits /public/jobs, not /jobs.
// Restricted server-side to status=open regardless of company.
export const publicJobsApi = {
  list: (params?: { page?: number; page_size?: number }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", String(params.page));
    if (params?.page_size) query.set("page_size", String(params.page_size));
    const qs = query.toString();
    return apiFetch<JobListResponse>(`/public/jobs${qs ? `?${qs}` : ""}`);
  },

  get: (jobId: string) => apiFetch<Job>(`/public/jobs/${jobId}`),
};
