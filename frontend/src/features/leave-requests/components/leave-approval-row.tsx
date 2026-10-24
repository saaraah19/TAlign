"use client";

import { useState } from "react";
import { Avatar } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useToast } from "@/components/ui/toast";
import { ApiError } from "@/lib/api-client";
import { useApproveLeaveRequest, useRejectLeaveRequest } from "../hooks/use-leave-requests";
import { formatDateRange, leaveDayCount } from "../lib/format-date-range";
import { LEAVE_TYPE_LABELS, type LeaveRequestWithEmployee } from "../types";
import { LeaveStatusBadge } from "./leave-status-badge";

/**
 * One request as a card-style row. Approving is one click; rejecting
 * asks for a second click in place, since neither decision can be
 * undone from here (same inline-confirm pattern used on candidates
 * and documents).
 */
export function LeaveApprovalRow({ leaveRequest }: { leaveRequest: LeaveRequestWithEmployee }) {
  const approve = useApproveLeaveRequest();
  const reject = useRejectLeaveRequest();
  const toast = useToast();
  const [error, setError] = useState<string | null>(null);
  const [confirmingReject, setConfirmingReject] = useState(false);

  const isPending = leaveRequest.status === "pending";
  const busy = approve.isPending || reject.isPending;
  const days = leaveDayCount(leaveRequest.start_date, leaveRequest.end_date);

  async function handleApprove() {
    setError(null);
    try {
      await approve.mutateAsync(leaveRequest.id);
      toast.success(`Approved ${leaveRequest.employee.first_name}'s request`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not approve this request.");
    }
  }

  async function handleReject() {
    setError(null);
    try {
      await reject.mutateAsync(leaveRequest.id);
      toast.success(`Rejected ${leaveRequest.employee.first_name}'s request`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not reject this request.");
      setConfirmingReject(false);
    }
  }

  return (
    <li className="px-5 py-4">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex min-w-0 items-start gap-3.5">
          <Avatar
            firstName={leaveRequest.employee.first_name}
            lastName={leaveRequest.employee.last_name}
            size={36}
          />
          <div className="min-w-0">
            <p className="text-sm font-medium text-ink">
              {leaveRequest.employee.first_name} {leaveRequest.employee.last_name}
              <span className="ml-2 text-xs font-normal text-ink/40">
                {leaveRequest.employee.job_title}
              </span>
            </p>
            <div className="mt-1.5 flex flex-wrap items-center gap-x-2.5 gap-y-1 text-sm text-ink/70">
              <Badge>{LEAVE_TYPE_LABELS[leaveRequest.leave_type]}</Badge>
              <span>{formatDateRange(leaveRequest.start_date, leaveRequest.end_date)}</span>
              <span className="text-ink/40">
                {days} {days === 1 ? "day" : "days"}
              </span>
            </div>
            {leaveRequest.reason && (
              <p className="mt-1.5 text-xs leading-relaxed text-ink/50">{leaveRequest.reason}</p>
            )}
          </div>
        </div>

        <div className="flex shrink-0 flex-wrap items-center gap-2">
          {!isPending && <LeaveStatusBadge status={leaveRequest.status} />}

          {isPending &&
            (confirmingReject ? (
              <>
                <span className="text-xs text-red-700">Reject this request?</span>
                <Button variant="danger" size="sm" onClick={handleReject} disabled={busy}>
                  {reject.isPending ? "Rejecting…" : "Confirm"}
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setConfirmingReject(false)}
                  disabled={busy}
                >
                  Cancel
                </Button>
              </>
            ) : (
              <>
                <Button size="sm" onClick={handleApprove} disabled={busy}>
                  {approve.isPending ? "Approving…" : "Approve"}
                </Button>
                <Button
                  variant="danger"
                  size="sm"
                  onClick={() => setConfirmingReject(true)}
                  disabled={busy}
                >
                  Reject
                </Button>
              </>
            ))}
        </div>
      </div>

      {error && <p className="mt-2 text-xs text-red-600">{error}</p>}
    </li>
  );
}
