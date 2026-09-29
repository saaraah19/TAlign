"use client";

import { useState } from "react";
import { ApiError } from "@/lib/api-client";
import {
  useApproveLeaveRequest,
  useLeaveRequestsPipeline,
  useRejectLeaveRequest,
} from "../hooks/use-leave-requests";
import {
  LEAVE_TYPE_LABELS,
  type LeaveRequestStatus,
  type LeaveRequestWithEmployee,
} from "../types";
import { LeaveStatusBadge } from "./leave-status-badge";

const FILTERS: { label: string; value: LeaveRequestStatus | undefined }[] = [
  { label: "Pending", value: "pending" },
  { label: "Approved", value: "approved" },
  { label: "Rejected", value: "rejected" },
  { label: "All", value: undefined },
];

export function LeaveApprovalQueue() {
  const [status, setStatus] = useState<LeaveRequestStatus | undefined>("pending");
  const { data, isLoading, error } = useLeaveRequestsPipeline(status ? { status } : undefined);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex gap-2">
        {FILTERS.map((filter) => (
          <button
            key={filter.label}
            type="button"
            onClick={() => setStatus(filter.value)}
            className={`rounded-full px-3 py-1 text-xs font-medium ${
              status === filter.value
                ? "bg-gray-900 text-white"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
          >
            {filter.label}
          </button>
        ))}
      </div>

      {isLoading && <p className="text-sm text-gray-500">Loading leave requests…</p>}
      {error && <p className="text-sm text-red-600">Could not load leave requests.</p>}
      {data && data.items.length === 0 && (
        <p className="text-sm text-gray-500">No leave requests here.</p>
      )}

      {data && data.items.length > 0 && (
        <ul className="divide-y divide-gray-200 rounded-lg border border-gray-200">
          {data.items.map((leaveRequest) => (
            <LeaveApprovalRow key={leaveRequest.id} leaveRequest={leaveRequest} />
          ))}
        </ul>
      )}
    </div>
  );
}

function LeaveApprovalRow({ leaveRequest }: { leaveRequest: LeaveRequestWithEmployee }) {
  const approve = useApproveLeaveRequest();
  const reject = useRejectLeaveRequest();
  const [rowError, setRowError] = useState<string | null>(null);

  const isPending = leaveRequest.status === "pending";
  const busy = approve.isPending || reject.isPending;

  async function handleApprove() {
    setRowError(null);
    try {
      await approve.mutateAsync(leaveRequest.id);
    } catch (err) {
      setRowError(err instanceof ApiError ? err.message : "Could not approve this request.");
    }
  }

  async function handleReject() {
    setRowError(null);
    try {
      await reject.mutateAsync(leaveRequest.id);
    } catch (err) {
      setRowError(err instanceof ApiError ? err.message : "Could not reject this request.");
    }
  }

  return (
    <li className="flex flex-col gap-2 px-4 py-3 text-sm sm:flex-row sm:items-center sm:justify-between">
      <div>
        <p className="font-medium text-gray-900">
          {leaveRequest.employee.first_name} {leaveRequest.employee.last_name}
        </p>
        <p className="text-gray-500">
          {LEAVE_TYPE_LABELS[leaveRequest.leave_type]} ·{" "}
          {new Date(leaveRequest.start_date).toLocaleDateString()} –{" "}
          {new Date(leaveRequest.end_date).toLocaleDateString()}
        </p>
        {leaveRequest.reason && <p className="text-gray-500">{leaveRequest.reason}</p>}
      </div>

      <div className="flex items-center gap-3">
        <LeaveStatusBadge status={leaveRequest.status} />

        {rowError && <p className="text-xs text-red-600">{rowError}</p>}

        {isPending && (
          <>
            <button
              type="button"
              onClick={handleApprove}
              disabled={busy}
              className="rounded-md bg-gray-900 px-3 py-1.5 text-xs font-medium text-white disabled:opacity-50"
            >
              Approve
            </button>
            <button
              type="button"
              onClick={handleReject}
              disabled={busy}
              className="rounded-md border border-red-300 px-3 py-1.5 text-xs font-medium text-red-600 disabled:opacity-50"
            >
              Reject
            </button>
          </>
        )}
      </div>
    </li>
  );
}
