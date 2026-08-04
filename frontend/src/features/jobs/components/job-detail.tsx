"use client";

import { useState } from "react";
import { ApiError } from "@/lib/api-client";
import { useDeleteJob, useJob, useTransitionJob } from "../hooks/use-jobs";
import {
  CURRENCY_SYMBOLS,
  EMPLOYMENT_TYPE_LABELS,
  JOB_STATUS_LABELS,
  JOB_STATUS_TRANSITIONS,
} from "../types";
import { JobStatusBadge } from "./job-status-badge";

export function JobDetail({ jobId, onDeleted }: { jobId: string; onDeleted?: () => void }) {
  const { data: job, isLoading, error } = useJob(jobId);
  const transitionJob = useTransitionJob(jobId);
  const deleteJob = useDeleteJob();
  const [actionError, setActionError] = useState<string | null>(null);

  if (isLoading) return <p className="text-sm text-gray-500">Loading…</p>;
  if (error || !job) return <p className="text-sm text-red-600">Could not load this job.</p>;

  // The UI reads the same transition graph the backend enforces — it
  // can only ever offer the single legal next status (or none, if
  // ARCHIVED). This doesn't replace backend validation; it just means a
  // user never sees a button that would fail.
  const nextStatus = JOB_STATUS_TRANSITIONS[job.status];

  async function handleTransition() {
    if (!nextStatus) return;
    setActionError(null);
    try {
      await transitionJob.mutateAsync(nextStatus);
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
      onDeleted?.();
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Delete failed.");
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">{job.title}</h1>
        <JobStatusBadge status={job.status} />
      </div>

      <p className="text-sm text-gray-500">
        {EMPLOYMENT_TYPE_LABELS[job.employment_type]}
        {job.location ? ` · ${job.location}` : ""}
        {job.salary_min || job.salary_max
          ? ` · ${CURRENCY_SYMBOLS[job.salary_currency]}${job.salary_min ?? "?"} – ${CURRENCY_SYMBOLS[job.salary_currency]}${job.salary_max ?? "?"}`
          : ""}
      </p>

      <p className="whitespace-pre-wrap text-sm text-gray-700">{job.description}</p>

      {actionError && <p className="text-sm text-red-600">{actionError}</p>}

      <div className="flex gap-3 pt-2">
        {nextStatus && (
          <button
            onClick={handleTransition}
            disabled={transitionJob.isPending}
            className="rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
          >
            {transitionJob.isPending ? "Updating…" : `Move to ${JOB_STATUS_LABELS[nextStatus]}`}
          </button>
        )}

        {job.status === "draft" && (
          <button
            onClick={handleDelete}
            disabled={deleteJob.isPending}
            className="rounded-md border border-red-300 px-4 py-2 text-sm font-medium text-red-600 disabled:opacity-50"
          >
            {deleteJob.isPending ? "Deleting…" : "Delete draft"}
          </button>
        )}

        <a
          href={`/pipeline?job_id=${job.id}`}
          className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700"
        >
          View applicants
        </a>
      </div>
    </div>
  );
}
