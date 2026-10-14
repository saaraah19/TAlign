import { Badge } from "@/components/ui/badge";
import { JOB_STATUS_LABELS, type JobStatus } from "../types";

const STATUS_TONES = {
  draft: "neutral",
  open: "success",
  closed: "warning",
  archived: "neutral",
} as const;

export function JobStatusBadge({ status }: { status: JobStatus }) {
  return <Badge tone={STATUS_TONES[status]}>{JOB_STATUS_LABELS[status]}</Badge>;
}
