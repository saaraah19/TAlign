import { apiFetch } from "@/lib/api-client";
import type {
  AnalysisProgressStatus,
  ApplicationListResponse,
  ApplicationStatus,
  ApplicationWithCandidate,
  ApplicationWithJob,
  PipelineListResponse,
  ResumeAnalysis,
} from "./types";

export const applicationsApi = {
  apply: (jobId: string) =>
    apiFetch<ApplicationWithJob>("/applications", {
      method: "POST",
      body: JSON.stringify({ job_id: jobId }),
    }),

  listMine: (params?: { page?: number; page_size?: number }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", String(params.page));
    if (params?.page_size) query.set("page_size", String(params.page_size));
    const qs = query.toString();
    return apiFetch<ApplicationListResponse>(`/applications/mine${qs ? `?${qs}` : ""}`);
  },

  getMine: (applicationId: string) =>
    apiFetch<ApplicationWithJob>(`/applications/mine/${applicationId}`),

  listPipeline: (params?: { job_id?: string; status?: ApplicationStatus; page?: number }) => {
    const query = new URLSearchParams();
    if (params?.job_id) query.set("job_id", params.job_id);
    if (params?.status) query.set("status", params.status);
    if (params?.page) query.set("page", String(params.page));
    const qs = query.toString();
    return apiFetch<PipelineListResponse>(`/applications${qs ? `?${qs}` : ""}`);
  },

  get: (applicationId: string) =>
    apiFetch<ApplicationWithCandidate>(`/applications/${applicationId}`),

  transition: (applicationId: string, targetStatus: ApplicationStatus) =>
    apiFetch<ApplicationWithCandidate>(`/applications/${applicationId}/transition`, {
      method: "POST",
      body: JSON.stringify({ target_status: targetStatus }),
    }),

  // --- Slice 4: Resume Intelligence ---

  attachResume: (applicationId: string, resumeId: string) =>
    apiFetch<ApplicationWithJob>(`/applications/mine/${applicationId}/resume`, {
      method: "PUT",
      body: JSON.stringify({ resume_id: resumeId }),
    }),

  getMyAnalysisStatus: (applicationId: string) =>
    apiFetch<{ status: AnalysisProgressStatus }>(
      `/applications/mine/${applicationId}/analysis-status`,
    ),

  getAnalysisStatus: (applicationId: string) =>
    apiFetch<{ status: AnalysisProgressStatus }>(`/applications/${applicationId}/analysis-status`),

  getAnalysis: (applicationId: string) =>
    apiFetch<ResumeAnalysis>(`/applications/${applicationId}/analysis`),

  getAnalysisHistory: (applicationId: string) =>
    apiFetch<{ items: ResumeAnalysis[] }>(`/applications/${applicationId}/analysis/history`),

  reanalyze: (applicationId: string) =>
    apiFetch<{ status: AnalysisProgressStatus }>(`/applications/${applicationId}/reanalyze`, {
      method: "POST",
    }),
};
