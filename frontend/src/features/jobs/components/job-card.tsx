import Link from "next/link";
import { Card } from "@/components/ui/card";
import { EMPLOYMENT_TYPE_LABELS, type JobWithStats } from "../types";
import { JobStatusBadge } from "./job-status-badge";

const NOTABLE_STAGES: { key: string; label: string }[] = [
  { key: "screening", label: "screening" },
  { key: "interview", label: "interview" },
];

export function JobCard({ job }: { job: JobWithStats }) {
  return (
    <Card className="flex flex-col gap-3 p-5 transition-colors hover:border-ink/25">
      <Link href={`/jobs/${job.id}`} className="flex items-start justify-between gap-3">
        <div>
          <p className="font-medium text-ink">{job.title}</p>
          <p className="mt-0.5 text-sm text-ink/50">
            {EMPLOYMENT_TYPE_LABELS[job.employment_type]}
            {job.location ? ` · ${job.location}` : ""}
          </p>
        </div>
        <JobStatusBadge status={job.status} />
      </Link>

      <div className="flex flex-wrap items-center justify-between gap-y-2">
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-ink/55">
          <span className="font-medium text-ink">
            {job.applicant_count} applicant{job.applicant_count === 1 ? "" : "s"}
          </span>
          {NOTABLE_STAGES.map((stage) => {
            const count = job.stage_counts[stage.key] ?? 0;
            if (count === 0) return null;
            return (
              <span key={stage.key}>
                {count} {stage.label}
              </span>
            );
          })}
        </div>
        {job.applicant_count > 0 && (
          <Link
            href={`/pipeline?job_id=${job.id}`}
            className="text-xs font-medium text-ink/60 underline underline-offset-2 hover:text-ink"
          >
            View pipeline →
          </Link>
        )}
      </div>
    </Card>
  );
}
