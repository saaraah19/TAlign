import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { applicationsApi } from "../api";
import type { ApplicationStatus } from "../types";

export function useMyApplications(params?: { page?: number }) {
  return useQuery({
    queryKey: ["applications", "mine", params],
    queryFn: () => applicationsApi.listMine(params),
  });
}

export function useApplyToJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (jobId: string) => applicationsApi.apply(jobId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["applications", "mine"] });
    },
  });
}

export function usePipeline(params?: {
  job_id?: string;
  status?: ApplicationStatus;
  page?: number;
}) {
  return useQuery({
    queryKey: ["applications", "pipeline", params],
    queryFn: () => applicationsApi.listPipeline(params),
  });
}

export function useApplication(applicationId: string) {
  return useQuery({
    queryKey: ["applications", applicationId],
    queryFn: () => applicationsApi.get(applicationId),
    enabled: Boolean(applicationId),
  });
}

export function useTransitionApplication(applicationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (targetStatus: ApplicationStatus) =>
      applicationsApi.transition(applicationId, targetStatus),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["applications", applicationId] });
      queryClient.invalidateQueries({ queryKey: ["applications", "pipeline"] });
    },
  });
}

// --- Slice 4: Resume Intelligence ---

const ACTIVE_PROGRESS_STATES = new Set(["parsing", "analyzing"]);

export function useAttachResume(applicationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (resumeId: string) => applicationsApi.attachResume(applicationId, resumeId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["applications", "mine", applicationId] });
      queryClient.invalidateQueries({
        queryKey: ["applications", "mine", applicationId, "analysis-status"],
      });
    },
  });
}

/** Candidate-facing progress polling — status only, never analysis content. */
export function useMyAnalysisStatus(applicationId: string) {
  return useQuery({
    queryKey: ["applications", "mine", applicationId, "analysis-status"],
    queryFn: () => applicationsApi.getMyAnalysisStatus(applicationId),
    enabled: Boolean(applicationId),
    refetchInterval: (query) =>
      query.state.data && ACTIVE_PROGRESS_STATES.has(query.state.data.status) ? 2000 : false,
  });
}

/** Recruiter-facing progress polling — same derivation, different endpoint/RBAC. */
export function useAnalysisStatus(applicationId: string) {
  return useQuery({
    queryKey: ["applications", applicationId, "analysis-status"],
    queryFn: () => applicationsApi.getAnalysisStatus(applicationId),
    enabled: Boolean(applicationId),
    refetchInterval: (query) =>
      query.state.data && ACTIVE_PROGRESS_STATES.has(query.state.data.status) ? 2000 : false,
  });
}

export function useAnalysis(applicationId: string, enabled: boolean) {
  return useQuery({
    queryKey: ["applications", applicationId, "analysis"],
    queryFn: () => applicationsApi.getAnalysis(applicationId),
    enabled: enabled && Boolean(applicationId),
  });
}

export function useAnalysisHistory(applicationId: string) {
  return useQuery({
    queryKey: ["applications", applicationId, "analysis-history"],
    queryFn: () => applicationsApi.getAnalysisHistory(applicationId),
    enabled: Boolean(applicationId),
  });
}

export function useReanalyze(applicationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => applicationsApi.reanalyze(applicationId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["applications", applicationId, "analysis-status"],
      });
    },
  });
}
