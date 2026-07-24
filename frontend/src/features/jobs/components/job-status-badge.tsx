import { JOB_STATUS_LABELS, type JobStatus } from "../types";

const STATUS_STYLES: Record<JobStatus, string> = {
  draft: "bg-gray-100 text-gray-700",
  open: "bg-green-100 text-green-700",
  closed: "bg-amber-100 text-amber-700",
  archived: "bg-gray-100 text-gray-400",
};

export function JobStatusBadge({ status }: { status: JobStatus }) {
  return (
    <span
      className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_STYLES[status]}`}
    >
      {JOB_STATUS_LABELS[status]}
    </span>
  );
}
