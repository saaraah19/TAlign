export type LeaveRequestStatus = "pending" | "approved" | "rejected" | "cancelled";
export type LeaveType = "vacation" | "sick" | "personal";

// Mirrors backend LeaveRequestService._ALLOWED_TRANSITIONS exactly.
// PENDING is the only non-terminal state.
export const LEAVE_STATUS_LABELS: Record<LeaveRequestStatus, string> = {
  pending: "Pending",
  approved: "Approved",
  rejected: "Rejected",
  cancelled: "Cancelled",
};

export const LEAVE_TYPE_LABELS: Record<LeaveType, string> = {
  vacation: "Vacation",
  sick: "Sick leave",
  personal: "Personal",
};

export interface EmployeeSummary {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  job_title: string;
  hire_date: string;
}

export interface LeaveRequest {
  id: string;
  employee_id: string;
  company_id: string;
  start_date: string;
  end_date: string;
  leave_type: LeaveType;
  reason: string | null;
  status: LeaveRequestStatus;
  reviewed_by: string | null;
  reviewed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface LeaveRequestWithEmployee extends LeaveRequest {
  employee: EmployeeSummary;
}

export interface LeaveRequestListResponse {
  items: LeaveRequest[];
  total: number;
  page: number;
  page_size: number;
}

export interface LeaveRequestPipelineListResponse {
  items: LeaveRequestWithEmployee[];
  total: number;
  page: number;
  page_size: number;
}

export interface LeaveBalance {
  year: number;
  annual_allotment: number;
  days_used: number;
  days_remaining: number;
}

export interface CreateLeaveRequestInput {
  start_date: string;
  end_date: string;
  leave_type: LeaveType;
  reason?: string;
}
