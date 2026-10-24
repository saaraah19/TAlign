"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useLeaveRequestCounts, useLeaveRequestsPipeline } from "../hooks/use-leave-requests";
import type { LeaveRequestStatus } from "../types";
import { LeaveApprovalRow } from "./leave-approval-row";

type Tab = "pending" | "approved" | "rejected" | "all";

const TABS: { label: string; value: Tab }[] = [
  { label: "Pending", value: "pending" },
  { label: "Approved", value: "approved" },
  { label: "Rejected", value: "rejected" },
  { label: "All", value: "all" },
];

const EMPTY_MESSAGES: Record<Tab, { title: string; body: string }> = {
  pending: {
    title: "You're all caught up",
    body: "No requests are waiting for review. New ones will show up here as employees submit them.",
  },
  approved: {
    title: "Nothing approved yet",
    body: "Requests you approve will be listed here.",
  },
  rejected: {
    title: "Nothing rejected",
    body: "Requests you reject will be listed here.",
  },
  all: {
    title: "No leave requests yet",
    body: "When an employee requests time off, it will appear here for review.",
  },
};

/**
 * The approval queue: a summary sentence, status tabs with real
 * counts, then the requests for the selected tab (20 per page, with a
 * pager when there are more — the counts shown on the tabs are the
 * backend's own totals, so a tab can never promise more than it lists).
 */
export function LeaveApprovalQueue() {
  const [tab, setTab] = useState<Tab>("pending");
  const [page, setPage] = useState(1);
  const counts = useLeaveRequestCounts();
  const status: LeaveRequestStatus | undefined = tab === "all" ? undefined : tab;
  const { data, isLoading, error } = useLeaveRequestsPipeline({ status, page });

  function selectTab(next: Tab) {
    setTab(next);
    setPage(1);
  }

  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1;

  // Acting on the last request of the last page shrinks the list under
  // us (approve the only row on page 2 and page 2 no longer exists).
  // Step back to the last real page instead of showing an empty one.
  useEffect(() => {
    if (data && page > totalPages) setPage(totalPages);
  }, [data, page, totalPages]);

  return (
    <div className="flex flex-col gap-5">
      {counts.pending !== undefined && (
        <p className="text-sm text-ink/60">
          {counts.pending > 0 ? (
            <>
              <span className="font-medium text-ink">{counts.pending}</span>{" "}
              {counts.pending === 1 ? "request is" : "requests are"} waiting for your review.
            </>
          ) : (
            "No requests are waiting for review."
          )}
        </p>
      )}

      <div className="flex flex-wrap gap-2" role="group" aria-label="Filter by status">
        {TABS.map(({ label, value }) => {
          const active = tab === value;
          const count = counts[value];
          return (
            <button
              key={value}
              type="button"
              onClick={() => selectTab(value)}
              aria-pressed={active}
              className={`rounded-full px-3.5 py-1.5 text-xs font-medium transition-colors ${
                active ? "bg-ink text-white" : "bg-ink/[0.05] text-ink/65 hover:bg-ink/[0.09]"
              }`}
            >
              {label}
              {count !== undefined && (
                <span className={`ml-1.5 ${active ? "text-white/60" : "text-ink/35"}`}>
                  {count}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {isLoading && (
        <div className="flex flex-col gap-3">
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-20 w-full" />
          ))}
        </div>
      )}

      {error && <p className="text-sm text-red-600">Could not load leave requests.</p>}

      {data && data.items.length === 0 && page <= totalPages && (
        <EmptyState title={EMPTY_MESSAGES[tab].title} description={EMPTY_MESSAGES[tab].body} />
      )}

      {data && data.items.length > 0 && (
        <ul className="divide-y divide-line rounded-lg border border-line bg-white">
          {data.items.map((leaveRequest) => (
            <LeaveApprovalRow key={leaveRequest.id} leaveRequest={leaveRequest} />
          ))}
        </ul>
      )}

      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-xs text-ink/45">
            Page {page} of {totalPages}
          </p>
          <div className="flex gap-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setPage((p) => p - 1)}
              disabled={page <= 1}
            >
              Previous
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setPage((p) => p + 1)}
              disabled={page >= totalPages}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
