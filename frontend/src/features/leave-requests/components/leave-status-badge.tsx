import { LEAVE_STATUS_LABELS, type LeaveRequestStatus } from "../types";

const STATUS_STYLES: Record<LeaveRequestStatus, string> = {
  pending: "bg-amber-100 text-amber-700",
  approved: "bg-green-100 text-green-700",
  rejected: "bg-red-100 text-red-700",
  cancelled: "bg-gray-100 text-gray-500",
};

export function LeaveStatusBadge({ status }: { status: LeaveRequestStatus }) {
  return (
    <span
      className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_STYLES[status]}`}
    >
      {LEAVE_STATUS_LABELS[status]}
    </span>
  );
}
