"use client";

import { EmptyState } from "@/components/ui/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import { ApiError } from "@/lib/api-client";
import { useCancelMyLeaveRequest, useMyLeaveRequests } from "../hooks/use-leave-requests";
import { LEAVE_TYPE_LABELS } from "../types";
import { LeaveStatusBadge } from "./leave-status-badge";

export function MyLeaveRequestsList() {
  const { data, isLoading, error } = useMyLeaveRequests();
  const cancelLeaveRequest = useCancelMyLeaveRequest();
  const toast = useToast();

  if (isLoading) {
    return (
      <div className="flex flex-col gap-3">
        <Skeleton className="h-14 w-full" />
        <Skeleton className="h-14 w-full" />
      </div>
    );
  }
  if (error) return <p className="text-sm text-red-600">Could not load your leave requests.</p>;
  if (!data || data.items.length === 0) {
    return (
      <EmptyState
        title="No leave requests yet"
        description="Use the form above to request time off — you'll follow its status here."
      />
    );
  }

  async function handleCancel(id: string) {
    try {
      await cancelLeaveRequest.mutateAsync(id);
      toast.success("Leave request cancelled");
    } catch (err) {
      // A list row has no natural spot for an inline message, so this
      // is the one place an error uses a toast (it replaced alert()).
      toast.error(err instanceof ApiError ? err.message : "Could not cancel this request.");
    }
  }

  return (
    <ul className="divide-y divide-gray-200 rounded-lg border border-gray-200">
      {data.items.map((leaveRequest) => (
        <li
          key={leaveRequest.id}
          className="flex flex-col gap-2 px-4 py-3 text-sm sm:flex-row sm:items-center sm:justify-between"
        >
          <div>
            <p className="font-medium text-gray-900">
              {LEAVE_TYPE_LABELS[leaveRequest.leave_type]} ·{" "}
              {new Date(leaveRequest.start_date).toLocaleDateString()} –{" "}
              {new Date(leaveRequest.end_date).toLocaleDateString()}
            </p>
            {leaveRequest.reason && <p className="text-gray-500">{leaveRequest.reason}</p>}
          </div>
          <div className="flex items-center gap-3">
            <LeaveStatusBadge status={leaveRequest.status} />
            {leaveRequest.status === "pending" && (
              <button
                type="button"
                onClick={() => handleCancel(leaveRequest.id)}
                disabled={cancelLeaveRequest.isPending}
                className="text-sm font-medium text-gray-500 underline disabled:opacity-50"
              >
                Cancel
              </button>
            )}
          </div>
        </li>
      ))}
    </ul>
  );
}
