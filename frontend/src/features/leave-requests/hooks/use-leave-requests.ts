import { useMutation, useQueries, useQuery, useQueryClient } from "@tanstack/react-query";
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

export function useLeaveRequestsPipeline(params?: {
  status?: LeaveRequestStatus;
  page?: number;
}) {
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

// --- Approval-queue summary counts ---

const COUNT_FILTERS: (LeaveRequestStatus | undefined)[] = [
  "pending",
  "approved",
  "rejected",
  undefined, // all
];

export interface LeaveRequestCounts {
  pending: number | undefined;
  approved: number | undefined;
  rejected: number | undefined;
  all: number | undefined;
}

/**
 * Real totals per status, with no new backend endpoint: the list
 * endpoint already returns `total` for whatever filter it's given, so
 * asking for one row per status costs four tiny requests and the
 * numbers are exactly what each tab will list. Keyed under
 * ["leave-requests", "pipeline"], so approving or rejecting a request
 * refreshes these along with the list.
 */
export function useLeaveRequestCounts(): LeaveRequestCounts {
  const results = useQueries({
    queries: COUNT_FILTERS.map((status) => ({
      queryKey: ["leave-requests", "pipeline", "count", status ?? "all"],
      queryFn: async () => (await leaveRequestsApi.listPipeline({ status, pageSize: 1 })).total,
    })),
  });
  return {
    pending: results[0]?.data,
    approved: results[1]?.data,
    rejected: results[2]?.data,
    all: results[3]?.data,
  };
}
