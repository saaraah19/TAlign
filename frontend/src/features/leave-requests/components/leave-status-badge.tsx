import { Badge } from "@/components/ui/badge";
import { LEAVE_STATUS_LABELS, type LeaveRequestStatus } from "../types";

const STATUS_TONES = {
  pending: "warning",
  approved: "success",
  rejected: "danger",
  cancelled: "neutral",
} as const;

export function LeaveStatusBadge({ status }: { status: LeaveRequestStatus }) {
  return <Badge tone={STATUS_TONES[status]}>{LEAVE_STATUS_LABELS[status]}</Badge>;
}
