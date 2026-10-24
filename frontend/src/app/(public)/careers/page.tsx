"use client";

import Link from "next/link";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import {
  EMPLOYMENT_TYPE_LABELS,
  formatSalaryRange,
  SkillChips,
  usePublicJobs,
} from "@/features/jobs";
import { formatRelativeTime } from "@/lib/format-relative-time";

export default function CareersPage() {
  const [page, setPage] = useState(1);
  const { data, isLoading, error } = usePublicJobs({ page });

  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1;

  return (
    <main className="mx-auto max-w-4xl px-6 py-10 sm:px-8">
      <h1 className="text-2xl font-semibold tracking-tight text-ink">Open positions</h1>
      <p className="mt-1 text-sm text-ink/55">
        {data
          ? `${data.total} open ${data.total === 1 ? "role" : "roles"} across every company on Talign.`
          : "Browse open roles across every company on Talign."}
      </p>

      <div className="mt-8">
        {isLoading && (
          <div className="flex flex-col gap-3">
            {[0, 1, 2].map((i) => (
              <Skeleton key={i} className="h-28 w-full" />
            ))}
          </div>
        )}

        {error && (
          <p className="text-sm text-red-600">
            We couldn&apos;t load the job board. Please try again in a moment.
          </p>
        )}

        {data && data.items.length === 0 && (
          <EmptyState
            title="No open positions right now"
            description="New roles appear here as soon as companies publish them, so it's worth checking back."
          />
        )}

        {data && data.items.length > 0 && (
          <ul className="flex flex-col gap-3">
            {data.items.map((job) => {
              const salary = formatSalaryRange(job);
              return (
                <li key={job.id}>
                  <Link
                    href={`/careers/${job.id}`}
                    className="block rounded-lg border border-line bg-white p-5 transition-colors hover:border-ink/30"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="min-w-0">
                        <p className="text-base font-medium text-ink">{job.title}</p>
                        <p className="mt-1 text-sm text-ink/55">
                          <span className="font-medium text-ink/75">{job.company_name}</span>
                          {" · "}
                          {EMPLOYMENT_TYPE_LABELS[job.employment_type]}
                          {job.location ? ` · ${job.location}` : ""}
                          {salary ? ` · ${salary}` : ""}
                        </p>
                      </div>
                      <span className="shrink-0 text-xs text-ink/40">
                        {formatRelativeTime(job.created_at)}
                      </span>
                    </div>
                    <SkillChips skills={job.required_skills} max={4} className="mt-3" />
                  </Link>
                </li>
              );
            })}
          </ul>
        )}

        {totalPages > 1 && (
          <div className="mt-6 flex items-center justify-between">
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
    </main>
  );
}
