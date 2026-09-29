import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { leaveRequestsApi } from "../api";
import type { CreateLeaveRequestInput, LeaveRequestStatus } from "../types";

// --- Employee-facing (portal self-service) ---

export function useMyLeaveRequests(params?: { page?: number }) {
  return useQuery({
    queryKey: ["leave-requests", "mine", params],
    queryFn: () => leaveRequestsApi.listMine(params),
  });
}

export function useMyLeaveBalance(year?: number) {
  return useQuery({
    queryKey: ["leave-requests", "mine", "balance", year],
    queryFn: () => leaveRequestsApi.getMyBalance(year),
  });
}

export function useCreateLeaveRequest() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: CreateLeaveRequestInput) => leaveRequestsApi.create(input),
    // onSettled (not onSuccess): re-syncs with real server state whether
    // the client believes the request succeeded or not — same reasoning
    // as useTransitionJob (features/jobs), the documented precedent for
    // this pattern in this codebase.
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["leave-requests", "mine"] });
    },
  });
}

export function useCancelMyLeaveRequest() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (leaveRequestId: string) => leaveRequestsApi.cancelMine(leaveRequestId),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["leave-requests", "mine"] });
    },
  });
}

// --- Admin/hiring-manager-facing (approval queue) ---

export function useLeaveRequestsPipeline(params?: { status?: LeaveRequestStatus; page?: number }) {
  return useQuery({
    queryKey: ["leave-requests", "pipeline", params],
    queryFn: () => leaveRequestsApi.listPipeline(params),
  });
}

export function useApproveLeaveRequest() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (leaveRequestId: string) => leaveRequestsApi.approve(leaveRequestId),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["leave-requests", "pipeline"] });
    },
  });
}

export function useRejectLeaveRequest() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (leaveRequestId: string) => leaveRequestsApi.reject(leaveRequestId),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["leave-requests", "pipeline"] });
    },
  });
}
