"use client";

import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useMyLeaveBalance } from "../hooks/use-leave-requests";

/**
 * Simple fixed-allotment balance — see backend LeaveRequestService's
 * module docstring. `days_remaining` is shown as-is, including negative
 * values (an admin can approve a request past the allotment; this
 * deliberately doesn't hide that behind a floor of zero). The bar is
 * drawn from the same two real numbers (used / allotment), nothing else.
 */
export function LeaveBalanceCard() {
  const { data, isLoading, error } = useMyLeaveBalance();

  if (isLoading) return <Skeleton className="h-32 w-full" />;
  if (error || !data) {
    return <p className="text-sm text-red-600">Could not load your leave balance.</p>;
  }

  const isOver = data.days_remaining < 0;
  const usedPct =
    data.annual_allotment > 0
      ? Math.min(100, Math.max(0, (data.days_used / data.annual_allotment) * 100))
      : 0;

  return (
    <Card className="p-6">
      <div className="flex flex-wrap items-end justify-between gap-x-6 gap-y-2">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-ink/45">
            Leave balance · {data.year}
          </p>
          <p
            className={`mt-1.5 text-4xl font-semibold tracking-tight ${
              isOver ? "text-red-600" : "text-ink"
            }`}
          >
            {data.days_remaining}
            <span className="ml-2 text-base font-normal text-ink/50">
              {Math.abs(data.days_remaining) === 1 ? "day" : "days"} remaining
            </span>
          </p>
        </div>
        <p className="text-sm text-ink/50">
          {data.days_used} of {data.annual_allotment} used this year
        </p>
      </div>

      <div
        className="mt-5 h-2 w-full rounded-full bg-ink/[0.07]"
        role="img"
        aria-label={`${data.days_used} of ${data.annual_allotment} leave days used`}
      >
        <div
          className={`h-2 rounded-full transition-[width] duration-700 ease-out ${
            isOver ? "bg-red-500" : "bg-ink"
          }`}
          style={{ width: `${usedPct}%` }}
        />
      </div>
      {isOver && (
        <p className="mt-3 text-xs text-red-600">
          You&apos;re {Math.abs(data.days_remaining)}{" "}
          {Math.abs(data.days_remaining) === 1 ? "day" : "days"} over your yearly allotment.
        </p>
      )}
    </Card>
  );
}
