"use client";

import Link from "next/link";
import { buttonClasses } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { formatRelativeTime } from "@/lib/format-relative-time";
import { useMyApplications } from "../hooks/use-applications";
import { ApplicationStatusBadge } from "./application-status-badge";

export function MyApplicationsList() {
  const { data, isLoading, error } = useMyApplications();

  if (isLoading) {
    return (
      <div className="flex flex-col gap-3">
        <Skeleton className="h-20 w-full" />
        <Skeleton className="h-20 w-full" />
      </div>
    );
  }
  if (error) return <p className="text-sm text-red-600">Could not load your applications.</p>;
  if (!data || data.items.length === 0) {
    return (
      <EmptyState
        title="No applications yet"
        description="When you apply to a role, you can follow each step of the process right here."
        action={
          <Link href="/careers" className={buttonClasses("primary", "sm")}>
            Browse open positions
          </Link>
        }
      />
    );
  }

  return (
    <ul className="flex flex-col gap-3">
      {data.items.map((application) => (
        <li key={application.id}>
          <Link
            href={`/applications/${application.id}`}
            className="flex items-center justify-between gap-4 rounded-lg border border-line bg-white p-5 transition-colors hover:border-ink/30"
          >
            <div className="min-w-0">
              <p className="truncate text-base font-medium text-ink">{application.job.title}</p>
              <p className="mt-1 text-sm text-ink/50">
                Applied {formatRelativeTime(application.created_at)}
              </p>
            </div>
            <ApplicationStatusBadge status={application.status} />
          </Link>
        </li>
      ))}
    </ul>
  );
}
