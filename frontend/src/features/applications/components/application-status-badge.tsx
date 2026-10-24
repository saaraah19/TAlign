import { Badge } from "@/components/ui/badge";
import { APPLICATION_STATUS_LABELS, type ApplicationStatus } from "../types";

const STATUS_TONES = {
  applied: "neutral",
  screening: "info",
  interview: "accent",
  offer: "warning",
  hired: "success",
  rejected: "danger",
} as const;

export function ApplicationStatusBadge({ status }: { status: ApplicationStatus }) {
  return <Badge tone={STATUS_TONES[status]}>{APPLICATION_STATUS_LABELS[status]}</Badge>;
}
