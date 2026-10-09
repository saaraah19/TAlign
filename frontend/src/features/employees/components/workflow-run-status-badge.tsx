import { Badge } from "@/components/ui/badge";
import { WORKFLOW_RUN_STATUS_LABELS, type WorkflowRunStatus } from "../types";

const STATUS_TONES = {
  success: "success",
  failed: "danger",
  skipped: "neutral",
} as const;

export function WorkflowRunStatusBadge({ status }: { status: WorkflowRunStatus }) {
  return <Badge tone={STATUS_TONES[status]}>{WORKFLOW_RUN_STATUS_LABELS[status]}</Badge>;
}
