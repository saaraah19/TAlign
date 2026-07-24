"use client";

import { useState } from "react";
import Link from "next/link";
import { ApiError } from "@/lib/api-client";
import { usePipeline, useTransitionApplication } from "../hooks/use-applications";
import {
  APPLICATION_CAN_REJECT,
  APPLICATION_FORWARD_TRANSITIONS,
  APPLICATION_STATUS_LABELS,
  type ApplicationStatus,
} from "../types";
import { ApplicationStatusBadge } from "./application-status-badge";

export function PipelineView({ jobId }: { jobId?: string }) {
  const { data, isLoading, error } = usePipeline(jobId ? { job_id: jobId } : undefined);

  if (isLoading) return <p className="text-sm text-gray-500">Loading pipeline…</p>;
  if (error) return <p className="text-sm text-red-600">Could not load the pipeline.</p>;
  if (!data || data.items.length === 0) {
    return <p className="text-sm text-gray-500">No applications yet.</p>;
  }

  return (
    <ul className="divide-y divide-gray-200 rounded-lg border border-gray-200">
      {data.items.map((application) => (
        <PipelineRow key={application.id} application={application} />
      ))}
    </ul>
  );
}

function PipelineRow({
  application,
}: {
  application: {
    id: string;
    status: ApplicationStatus;
    job: { title: string };
    candidate: { first_name: string; last_name: string; email: string };
    created_at: string;
  };
}) {
  const transition = useTransitionApplication(application.id);
  const [rowError, setRowError] = useState<string | null>(null);

  const nextStage = APPLICATION_FORWARD_TRANSITIONS[application.status];
  const canReject = APPLICATION_CAN_REJECT[application.status];

  async function handleTransition(target: ApplicationStatus) {
    setRowError(null);
    try {
      await transition.mutateAsync(target);
    } catch (err) {
      setRowError(err instanceof ApiError ? err.message : "Update failed.");
    }
  }

  return (
    <li className="flex flex-col gap-2 px-4 py-3 text-sm sm:flex-row sm:items-center sm:justify-between">
      <div>
        <Link href={`/pipeline/${application.id}`} className="font-medium text-gray-900 hover:underline">
          {application.candidate.first_name} {application.candidate.last_name}
        </Link>
        <p className="text-gray-500">
          {application.candidate.email} · {application.job.title}
        </p>
      </div>

      <div className="flex items-center gap-3">
        <ApplicationStatusBadge status={application.status} />

        {rowError && <p className="text-xs text-red-600">{rowError}</p>}

        {nextStage && (
          <button
            onClick={() => handleTransition(nextStage)}
            disabled={transition.isPending}
            className="rounded-md bg-gray-900 px-3 py-1.5 text-xs font-medium text-white disabled:opacity-50"
          >
            Move to {APPLICATION_STATUS_LABELS[nextStage]}
          </button>
        )}
        {canReject && (
          <button
            onClick={() => handleTransition("rejected")}
            disabled={transition.isPending}
            className="rounded-md border border-red-300 px-3 py-1.5 text-xs font-medium text-red-600 disabled:opacity-50"
          >
            Reject
          </button>
        )}
      </div>
    </li>
  );
}
