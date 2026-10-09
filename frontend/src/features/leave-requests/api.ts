import { apiFetch } from "@/lib/api-client";
import type {
  CreateLeaveRequestInput,
  LeaveBalance,
  LeaveRequest,
  LeaveRequestListResponse,
  LeaveRequestPipelineListResponse,
  LeaveRequestStatus,
  LeaveRequestWithEmployee,
} from "./types";

export const leaveRequestsApi = {
  // --- Employee-facing (portal self-service) ---

  create: (input: CreateLeaveRequestInput) =>
    apiFetch<LeaveRequest>("/leave-requests", {
      method: "POST",
      body: JSON.stringify(input),
    }),

  listMine: (params?: { page?: number; page_size?: number }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", String(params.page));
    if (params?.page_size) query.set("page_size", String(params.page_size));
    const qs = query.toString();
    return apiFetch<LeaveRequestListResponse>(`/leave-requests/mine${qs ? `?${qs}` : ""}`);
  },

  getMyBalance: (year?: number) => {
    const qs = year ? `?year=${year}` : "";
    return apiFetch<LeaveBalance>(`/leave-requests/mine/balance${qs}`);
  },

  cancelMine: (leaveRequestId: string) =>
    apiFetch<LeaveRequest>(`/leave-requests/${leaveRequestId}/cancel`, {
      method: "POST",
    }),

  // --- Admin/hiring-manager-facing (approval queue) ---

  listPipeline: (params?: { status?: LeaveRequestStatus; page?: number; pageSize?: number }) => {
    const query = new URLSearchParams();
    if (params?.status) query.set("status", params.status);
    if (params?.page) query.set("page", String(params.page));
    if (params?.pageSize) query.set("page_size", String(params.pageSize));
    const qs = query.toString();
    return apiFetch<LeaveRequestPipelineListResponse>(`/leave-requests${qs ? `?${qs}` : ""}`);
  },

  approve: (leaveRequestId: string) =>
    apiFetch<LeaveRequestWithEmployee>(`/leave-requests/${leaveRequestId}/approve`, {
      method: "POST",
    }),

  reject: (leaveRequestId: string) =>
    apiFetch<LeaveRequestWithEmployee>(`/leave-requests/${leaveRequestId}/reject`, {
      method: "POST",
    }),
};
