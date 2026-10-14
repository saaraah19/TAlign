"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useToast } from "@/components/ui/toast";
import { ApiError } from "@/lib/api-client";
import { useCancelMyLeaveRequest } from "../hooks/use-leave-requests";
import { formatDateRange, leaveDayCount } from "../lib/format-date-range";
import { LEAVE_TYPE_LABELS, type LeaveRequest } from "../types";
import { LeaveStatusBadge } from "./leave-status-badge";

/**
 * One of the employee's own requests. Cancelling can't be undone (a
 * cancelled request is closed; they'd have to submit a new one), so it
 * asks for a second click in place, like every other irreversible
 * action in the app.
 */
export function MyLeaveRequestRow({ leaveRequest }: { leaveRequest: LeaveRequest }) {
  const cancel = useCancelMyLeaveRequest();
  const toast = useToast();
  const [confirming, setConfirming] = useState(false);

  const days = leaveDayCount(leaveRequest.start_date, leaveRequest.end_date);

  async function handleCancel() {
    try {
      await cancel.mutateAsync(leaveRequest.id);
      toast.success("Leave request cancelled");
    } catch (err) {
      // A list row has no natural spot for an inline message, so this
      // is one of the few places an error uses a toast.
      toast.error(err instanceof ApiError ? err.message : "Could not cancel this request.");
      setConfirming(false);
    }
  }

  return (
    <li className="flex flex-col gap-3 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-x-2.5 gap-y-1 text-sm text-ink/70">
          <Badge>{LEAVE_TYPE_LABELS[leaveRequest.leave_type]}</Badge>
          <span className="font-medium text-ink">
            {formatDateRange(leaveRequest.start_date, leaveRequest.end_date)}
          </span>
          <span className="text-ink/40">
            {days} {days === 1 ? "day" : "days"}
          </span>
        </div>
        {leaveRequest.reason && (
          <p className="mt-1.5 text-xs leading-relaxed text-ink/50">{leaveRequest.reason}</p>
        )}
      </div>

      <div className="flex shrink-0 flex-wrap items-center gap-2">
        <LeaveStatusBadge status={leaveRequest.status} />
        {leaveRequest.status === "pending" &&
          (confirming ? (
            <>
              <Button variant="danger" size="sm" onClick={handleCancel} disabled={cancel.isPending}>
                {cancel.isPending ? "Cancelling…" : "Cancel request"}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setConfirming(false)}
                disabled={cancel.isPending}
              >
                Keep it
              </Button>
            </>
          ) : (
            <Button variant="ghost" size="sm" onClick={() => setConfirming(true)}>
              Cancel
            </Button>
          ))}
      </div>
    </li>
  );
}
