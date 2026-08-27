import { WORKFLOW_RUN_STATUS_LABELS, type WorkflowRunStatus } from "../types";

const STATUS_STYLES: Record<WorkflowRunStatus, string> = {
  success: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-700",
  skipped: "bg-gray-100 text-gray-700",
};

export function WorkflowRunStatusBadge({ status }: { status: WorkflowRunStatus }) {
  return (
    <span
      className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_STYLES[status]}`}
    >
      {WORKFLOW_RUN_STATUS_LABELS[status]}
    </span>
  );
}
