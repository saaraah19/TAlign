"use client";

import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import {
  AnalysisDetail,
  APPLICATION_CAN_REJECT,
  APPLICATION_FORWARD_TRANSITIONS,
  APPLICATION_STATUS_LABELS,
  ApplicationStatusBadge,
  useApplication,
  useTransitionApplication,
  type ApplicationStatus,
} from "@/features/applications";
import { useAuth } from "@/features/auth";
import { CommunicationPanel } from "@/features/communication";
import { CompassAsk } from "@/features/compass";
import { ApiError } from "@/lib/api-client";

export default function ApplicationDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const { user, isLoading: authLoading } = useAuth();
  const { data: application, isLoading, error } = useApplication(params.id);
  const transition = useTransitionApplication(params.id);
  const [transitionError, setTransitionError] = useState<string | null>(null);

  if (authLoading || !user) return null;
  if (isLoading) return <main className="p-8 text-sm text-gray-500">Loading…</main>;
  if (error || !application) {
    return <main className="p-8 text-sm text-red-600">Could not load this application.</main>;
  }

  const nextStage = APPLICATION_FORWARD_TRANSITIONS[application.status];
  const canReject = APPLICATION_CAN_REJECT[application.status];

  async function handleTransition(target: ApplicationStatus) {
    setTransitionError(null);
    try {
      await transition.mutateAsync(target);
    } catch (err) {
      setTransitionError(err instanceof ApiError ? err.message : "Update failed.");
    }
  }

  return (
    <main className="mx-auto max-w-2xl p-8">
      <button onClick={() => router.back()} className="text-xs text-gray-400 underline">
        ← Back
      </button>

      <div className="mt-2 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">
            {application.candidate.first_name} {application.candidate.last_name}
          </h1>
          <p className="text-sm text-gray-500">
            {application.candidate.email} · {application.job.title}
          </p>
        </div>
        <ApplicationStatusBadge status={application.status} />
      </div>

      <div className="mt-4 flex gap-3">
        {nextStage && (
          <button
            onClick={() => handleTransition(nextStage)}
            disabled={transition.isPending}
            className="rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
          >
            Move to {APPLICATION_STATUS_LABELS[nextStage]}
          </button>
        )}
        {canReject && (
          <button
            onClick={() => handleTransition("rejected")}
            disabled={transition.isPending}
            className="rounded-md border border-red-300 px-4 py-2 text-sm font-medium text-red-600 disabled:opacity-50"
          >
            Reject
          </button>
        )}
      </div>
      {transitionError && <p className="mt-2 text-sm text-red-600">{transitionError}</p>}

      <div className="mt-8 flex flex-col gap-6">
        <div>
          <h2 className="mb-3 text-sm font-medium text-gray-900">Resume Intelligence</h2>
          <AnalysisDetail applicationId={application.id} />
        </div>

        <CommunicationPanel applicationId={application.id} />

        <CompassAsk applicationId={application.id} />
      </div>
    </main>
  );
}
