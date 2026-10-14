"use client";

import Link from "next/link";
import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button, buttonClasses } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import { ApiError } from "@/lib/api-client";
import { useDeleteJob, useJob, useTransitionJob } from "../hooks/use-jobs";
import { formatSalaryRange } from "../lib/format-salary";
import { EMPLOYMENT_TYPE_LABELS, JOB_STATUS_LABELS, JOB_STATUS_TRANSITIONS } from "../types";
import { JobStatusBadge } from "./job-status-badge";
import { SkillChips } from "./skill-chips";

export function JobDetail({ jobId, onDeleted }: { jobId: string; onDeleted?: () => void }) {
  const { data: job, isLoading, error } = useJob(jobId);
  const transitionJob = useTransitionJob(jobId);
  const deleteJob = useDeleteJob();
  const toast = useToast();
  const [actionError, setActionError] = useState<string | null>(null);
  const [confirmingDelete, setConfirmingDelete] = useState(false);

  if (isLoading) {
    return (
      <div className="flex flex-col gap-4">
        <Skeleton className="h-8 w-72" />
        <Skeleton className="h-48 w-full" />
      </div>
    );
  }
  if (error || !job) return <p className="text-sm text-red-600">Could not load this job.</p>;

  // The UI reads the same transition graph the backend enforces — it
  // can only ever offer the single legal next status (or none, if
  // ARCHIVED). This doesn't replace backend validation; it just means a
  // user never sees a button that would fail.
  const nextStatus = JOB_STATUS_TRANSITIONS[job.status];
  const salary = formatSalaryRange(job);

  async function handleTransition() {
    if (!nextStatus) return;
    setActionError(null);
    try {
      await transitionJob.mutateAsync(nextStatus);
      toast.success(`Job is now ${JOB_STATUS_LABELS[nextStatus].toLowerCase()}`);
    } catch (err) {
      // Logged in full so DevTools Console shows the real cause
      // directly — no more guessing from a generic fallback message.
      console.error("Job transition failed:", err);
      if (err instanceof ApiError) {
        setActionError(err.message);
      } else if (err instanceof Error) {
        setActionError(`Transition failed: ${err.message}`);
      } else {
        setActionError("Transition failed for an unknown reason — check the console.");
      }
    }
  }

  async function handleDelete() {
    setActionError(null);
    try {
      await deleteJob.mutateAsync(jobId);
      toast.success("Job deleted");
      onDeleted?.();
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Delete failed.");
      setConfirmingDelete(false);
    }
  }

  const busy = transitionJob.isPending || deleteJob.isPending;

  return (
    <div className="flex flex-col gap-6">
      <div>
        <Link href="/jobs" className="text-xs font-medium text-ink/45 hover:text-ink">
          ← All jobs
        </Link>
        <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <h1 className="text-2xl font-semibold tracking-tight text-ink">{job.title}</h1>
          <JobStatusBadge status={job.status} />
        </div>
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <Badge>{EMPLOYMENT_TYPE_LABELS[job.employment_type]}</Badge>
          {job.location && <Badge>{job.location}</Badge>}
          {salary && <Badge>{salary}</Badge>}
        </div>
      </div>

      <Card className="p-6">
        <h2 className="text-sm font-medium text-ink">Description</h2>
        <p className="mt-3 whitespace-pre-wrap text-sm leading-relaxed text-ink/70">
          {job.description}
        </p>
      </Card>

      <Card className="flex flex-col gap-5 p-6">
        <div>
          <h2 className="text-sm font-medium text-ink">Scoring criteria</h2>
          <p className="mt-1 text-xs text-ink/50">What Resume Intelligence scores candidates against.</p>
        </div>
        {job.required_skills.length > 0 ? (
          <div>
            <p className="text-xs text-ink/40">Required skills</p>
            <SkillChips skills={job.required_skills} className="mt-2" />
          </div>
        ) : (
          <p className="text-sm text-ink/50">No required skills were set for this job.</p>
        )}
        {job.preferred_skills.length > 0 && (
          <div>
            <p className="text-xs text-ink/40">Preferred skills</p>
            <SkillChips skills={job.preferred_skills} className="mt-2" />
          </div>
        )}
        {job.min_years_experience !== null && (
          <div>
            <p className="text-xs text-ink/40">Minimum experience</p>
            <p className="mt-1 text-sm font-medium text-ink">
              {job.min_years_experience} {job.min_years_experience === 1 ? "year" : "years"}
            </p>
          </div>
        )}
      </Card>

      {actionError && <p className="text-sm text-red-600">{actionError}</p>}

      <div className="flex flex-wrap items-center gap-3">
        {nextStatus && (
          <Button onClick={handleTransition} disabled={busy}>
            {transitionJob.isPending ? "Updating…" : `Move to ${JOB_STATUS_LABELS[nextStatus]}`}
          </Button>
        )}

        <Link href={`/pipeline?job_id=${job.id}`} className={buttonClasses("secondary", "md")}>
          View applicants
        </Link>

        {job.status === "draft" &&
          (confirmingDelete ? (
            <div className="flex items-center gap-2 rounded-md border border-red-200 bg-red-50/50 px-3 py-1.5">
              <span className="text-xs text-red-700">Delete this draft? This can&apos;t be undone.</span>
              <Button variant="danger" size="sm" onClick={handleDelete} disabled={busy}>
                {deleteJob.isPending ? "Deleting…" : "Confirm delete"}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setConfirmingDelete(false)}
                disabled={busy}
              >
                Cancel
              </Button>
            </div>
          ) : (
            <Button variant="danger" onClick={() => setConfirmingDelete(true)} disabled={busy}>
              Delete draft
            </Button>
          ))}
      </div>
    </div>
  );
}
