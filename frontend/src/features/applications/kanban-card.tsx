"use client";

import Link from "next/link";
import { useState } from "react";
import { Avatar } from "@/components/ui/avatar";
import { useToast } from "@/components/ui/toast";
import { ApiError } from "@/lib/api-client";
import { formatRelativeTime } from "@/lib/format-relative-time";
import { useMoveApplicationStage } from "../hooks/use-applications";
import {
  APPLICATION_CAN_REJECT,
  APPLICATION_FORWARD_TRANSITIONS,
  APPLICATION_STATUS_LABELS,
} from "../types";
import type { ApplicationStatus, ApplicationWithScore } from "../types";

function scoreColor(score: number): string {
  if (score >= 80) return "text-emerald-600";
  if (score >= 60) return "text-amber-600";
  return "text-ink/50";
}

export function KanbanCard({ application }: { application: ApplicationWithScore }) {
  const move = useMoveApplicationStage();
  const toast = useToast();
  const [error, setError] = useState<string | null>(null);
  const nextStage = APPLICATION_FORWARD_TRANSITIONS[application.status];
  const canReject = APPLICATION_CAN_REJECT[application.status];

  async function handleMove(e: React.MouseEvent, targetStatus: ApplicationStatus) {
    e.preventDefault();
    e.stopPropagation();
    setError(null);
    try {
      await move.mutateAsync({ applicationId: application.id, targetStatus });
      toast.success(
        targetStatus === "rejected"
          ? `${application.candidate.first_name} rejected`
          : `${application.candidate.first_name} moved to ${APPLICATION_STATUS_LABELS[targetStatus]}`,
      );
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not move this candidate.");
    }
  }

  return (
    <Link
      href={`/pipeline/${application.id}`}
      className="block rounded-lg border border-line bg-white p-3.5 transition-colors hover:border-ink/25"
    >
      <div className="flex items-start gap-2.5">
        <Avatar
          firstName={application.candidate.first_name}
          lastName={application.candidate.last_name}
          size={30}
        />
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium text-ink">
            {application.candidate.first_name} {application.candidate.last_name}
          </p>
          <p className="truncate text-xs text-ink/45">{application.job.title}</p>
        </div>
        {application.latest_score != null && (
          <span className={`shrink-0 text-xs font-semibold ${scoreColor(application.latest_score)}`}>
            {application.latest_score.toFixed(0)}%
          </span>
        )}
      </div>

      <div className="mt-3 flex items-center justify-between">
        <span className="text-[11px] text-ink/35">
          {formatRelativeTime(application.updated_at)}
        </span>
        <div className="flex gap-1.5">
          {canReject && (
            <button
              onClick={(e) => handleMove(e, "rejected")}
              disabled={move.isPending}
              className="rounded px-2 py-1 text-[11px] font-medium text-red-500 hover:bg-red-50 disabled:opacity-50"
            >
              Reject
            </button>
          )}
          {nextStage && (
            <button
              onClick={(e) => handleMove(e, nextStage)}
              disabled={move.isPending}
              className="rounded bg-ink/[0.06] px-2 py-1 text-[11px] font-medium text-ink hover:bg-ink/10 disabled:opacity-50"
            >
              Advance →
            </button>
          )}
        </div>
      </div>
      {error && <p className="mt-2 text-[11px] text-red-600">{error}</p>}
    </Link>
  );
}
