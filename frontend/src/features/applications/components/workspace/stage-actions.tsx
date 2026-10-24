"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { useToast } from "@/components/ui/toast";
import { ApiError } from "@/lib/api-client";
import { useTransitionApplication } from "../../hooks/use-applications";
import {
  APPLICATION_CAN_REJECT,
  APPLICATION_FORWARD_TRANSITIONS,
  APPLICATION_STATUS_LABELS,
  type ApplicationStatus,
} from "../../types";

/**
 * The two human decisions available at any stage: advance, or reject.
 * Rejecting is terminal and can't be undone, so it takes two clicks —
 * the button turns into an explicit confirmation in place. (A full
 * modal system is Phase 6 work; an inline confirm gives the same
 * protection against a mis-click without building that early.)
 */
export function StageActions({
  applicationId,
  status,
}: {
  applicationId: string;
  status: ApplicationStatus;
}) {
  const transition = useTransitionApplication(applicationId);
  const toast = useToast();
  const [error, setError] = useState<string | null>(null);
  const [confirmingReject, setConfirmingReject] = useState(false);

  const nextStage = APPLICATION_FORWARD_TRANSITIONS[status];
  const canReject = APPLICATION_CAN_REJECT[status];

  if (!nextStage && !canReject) return null;

  async function handleTransition(target: ApplicationStatus) {
    setError(null);
    try {
      await transition.mutateAsync(target);
      setConfirmingReject(false);
      toast.success(
        target === "rejected"
          ? "Application rejected"
          : `Moved to ${APPLICATION_STATUS_LABELS[target]}`,
      );
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Update failed.");
    }
  }

  return (
    <div className="flex flex-col gap-2">
      {nextStage && (
        <Button onClick={() => handleTransition(nextStage)} disabled={transition.isPending}>
          {transition.isPending && !confirmingReject
            ? "Moving…"
            : `Move to ${APPLICATION_STATUS_LABELS[nextStage]}`}
        </Button>
      )}

      {canReject &&
        (confirmingReject ? (
          <div className="rounded-md border border-red-200 bg-red-50/50 p-3">
            <p className="text-xs text-red-700">
              Reject this candidate? This can&apos;t be undone.
            </p>
            <div className="mt-2.5 flex gap-2">
              <Button
                variant="danger"
                size="sm"
                onClick={() => handleTransition("rejected")}
                disabled={transition.isPending}
              >
                {transition.isPending ? "Rejecting…" : "Confirm reject"}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setConfirmingReject(false)}
                disabled={transition.isPending}
              >
                Cancel
              </Button>
            </div>
          </div>
        ) : (
          <Button variant="danger" onClick={() => setConfirmingReject(true)}>
            Reject
          </Button>
        ))}

      {error && <p className="text-xs text-red-600">{error}</p>}
    </div>
  );
}
