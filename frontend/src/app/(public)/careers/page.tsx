"use client";

import Link from "next/link";
import { EmptyState } from "@/components/ui/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { EMPLOYMENT_TYPE_LABELS, usePublicJobs } from "@/features/jobs";

export default function CareersPage() {
  const { data, isLoading, error } = usePublicJobs();

  return (
    <main className="mx-auto max-w-3xl p-6 sm:p-8">
      <h1 className="text-xl font-semibold">Open positions</h1>
      <p className="mt-1 text-sm text-gray-500">
        Browse open roles across every company on Talign.
      </p>

      <div className="mt-6">
        {isLoading && (
          <div className="flex flex-col gap-3">
            {[0, 1, 2].map((i) => (
              <Skeleton key={i} className="h-16 w-full" />
            ))}
          </div>
        )}
        {error && <p className="text-sm text-red-600">Could not load jobs.</p>}
        {data && data.items.length === 0 && (
          <EmptyState
            title="No open positions right now"
            description="New roles appear here as soon as companies publish them, so it's worth checking back."
          />
        )}
        {data && data.items.length > 0 && (
          <ul className="divide-y divide-gray-200 rounded-lg border border-gray-200">
            {data.items.map((job) => (
              <li key={job.id}>
                <Link
                  href={`/careers/${job.id}`}
                  className="block px-4 py-3 text-sm hover:bg-gray-50"
                >
                  <p className="font-medium text-gray-900">{job.title}</p>
                  <p className="text-gray-500">
                    {EMPLOYMENT_TYPE_LABELS[job.employment_type]}
                    {job.location ? ` · ${job.location}` : ""}
                  </p>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    </main>
  );
}
