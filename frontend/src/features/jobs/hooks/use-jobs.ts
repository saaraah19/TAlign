import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { jobsApi, publicJobsApi } from "../api";
import type { JobCreateInput, JobStatus } from "../types";

const jobsKey = (params?: { status?: JobStatus; page?: number }) => ["jobs", params] as const;
const jobKey = (jobId: string) => ["jobs", jobId] as const;

export function useJobs(params?: { status?: JobStatus; page?: number }) {
  return useQuery({
    queryKey: jobsKey(params),
    queryFn: () => jobsApi.list(params),
  });
}

export function useJob(jobId: string) {
  return useQuery({
    queryKey: jobKey(jobId),
    queryFn: () => jobsApi.get(jobId),
    enabled: Boolean(jobId),
  });
}

export function useCreateJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: JobCreateInput) => jobsApi.create(input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
    },
  });
}

export function useTransitionJob(jobId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (targetStatus: JobStatus) => jobsApi.transition(jobId, targetStatus),
    // onSettled (not onSuccess): fires whether the mutation resolved or
    // rejected. If the client believes the request failed for any
    // reason (network blip, dev-server restart mid-response, a parse
    // error — see api-client.ts) while the backend actually committed
    // the transition, this still re-syncs the UI with real server
    // state within a second, instead of leaving stale data until a
    // manual refresh. Harmless in the genuine-failure case too, since
    // refetching an unchanged job is a no-op visually.
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: jobKey(jobId) });
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
    },
  });
}

export function useDeleteJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (jobId: string) => jobsApi.remove(jobId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
    },
  });
}

// --- Public, unauthenticated browsing ---

export function usePublicJobs(params?: { page?: number }) {
  return useQuery({
    queryKey: ["public-jobs", params],
    queryFn: () => publicJobsApi.list(params),
  });
}

export function usePublicJob(jobId: string) {
  return useQuery({
    queryKey: ["public-jobs", jobId],
    queryFn: () => publicJobsApi.get(jobId),
    enabled: Boolean(jobId),
  });
}
