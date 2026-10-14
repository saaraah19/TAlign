"use client";

import { EmptyState } from "@/components/ui/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useMyLeaveRequests } from "../hooks/use-leave-requests";
import { MyLeaveRequestRow } from "./my-leave-request-row";

export function MyLeaveRequestsList() {
  const { data, isLoading, error } = useMyLeaveRequests();

  if (isLoading) {
    return (
      <div className="flex flex-col gap-3">
        <Skeleton className="h-16 w-full" />
        <Skeleton className="h-16 w-full" />
      </div>
    );
  }
  if (error) return <p className="text-sm text-red-600">Could not load your leave requests.</p>;
  if (!data || data.items.length === 0) {
    return (
      <EmptyState
        title="No leave requests yet"
        description="Use the form to request time off — you'll follow its status here."
      />
    );
  }

  return (
    <ul className="divide-y divide-line rounded-lg border border-line bg-white">
      {data.items.map((leaveRequest) => (
        <MyLeaveRequestRow key={leaveRequest.id} leaveRequest={leaveRequest} />
      ))}
    </ul>
  );
}
