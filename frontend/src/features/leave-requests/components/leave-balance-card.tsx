"use client";

import { useMyLeaveBalance } from "../hooks/use-leave-requests";

/**
 * Simple fixed-allotment balance — see backend LeaveRequestService's
 * module docstring. `days_remaining` is shown as-is, including negative
 * values (an admin can approve a request past the allotment; this
 * deliberately doesn't hide that behind a floor of zero).
 */
export function LeaveBalanceCard() {
  const { data, isLoading, error } = useMyLeaveBalance();

  if (isLoading) return <p className="text-sm text-gray-500">Loading your leave balance…</p>;
  if (error || !data) {
    return <p className="text-sm text-red-600">Could not load your leave balance.</p>;
  }

  const isOverAllotment = data.days_remaining < 0;

  return (
    <div className="rounded-lg border border-gray-200 p-4">
      <p className="text-xs font-medium uppercase tracking-wide text-gray-500">
        Leave balance · {data.year}
      </p>
      <p className={`mt-1 text-2xl font-semibold ${isOverAllotment ? "text-red-600" : "text-gray-900"}`}>
        {data.days_remaining} days remaining
      </p>
      <p className="mt-1 text-sm text-gray-500">
        {data.days_used} of {data.annual_allotment} used this year
      </p>
    </div>
  );
}
