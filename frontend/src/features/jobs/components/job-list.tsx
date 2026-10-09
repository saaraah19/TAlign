"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { buttonClasses } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useJobs } from "../hooks/use-jobs";
import type { JobStatus } from "../types";
import { JobCard } from "./job-card";

const TABS: { label: string; value: JobStatus | undefined }[] = [
  { label: "Open", value: "open" },
  { label: "Draft", value: "draft" },
  { label: "Closed", value: "closed" },
  { label: "All", value: undefined },
];

export function JobList({ canCreate }: { canCreate: boolean }) {
  const [tab, setTab] = useState<JobStatus | undefined>("open");
  const [search, setSearch] = useState("");
  const { data, isLoading, error } = useJobs(tab ? { status: tab } : undefined);

  // Client-side only -- there's no search endpoint on the backend yet,
  // so this filters whatever page of jobs is already loaded rather
  // than pretending to search the whole company's job history.
  const filtered = useMemo(() => {
    if (!data) return [];
    const query = search.trim().toLowerCase();
    if (!query) return data.items;
    return data.items.filter((job) => job.title.toLowerCase().includes(query));
  }, [data, search]);

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex gap-1">
          {TABS.map((t) => (
            <button
              key={t.label}
              onClick={() => setTab(t.value)}
              className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                tab === t.value ? "bg-ink/[0.06] text-ink" : "text-ink/50 hover:text-ink"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search job titles…"
          className="w-full rounded-md border border-line px-3 py-2 text-sm placeholder:text-ink/30 focus:border-ink/30 focus:outline-none sm:w-64"
        />
      </div>

      {isLoading && (
        <div className="grid gap-4 sm:grid-cols-2">
          {[0, 1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-32 w-full" />
          ))}
        </div>
      )}
      {error && <p className="text-sm text-red-600">Could not load jobs.</p>}

      {data && filtered.length === 0 && (
        <EmptyState
          title={search ? "No jobs match your search" : "No jobs in this view yet"}
          description={
            search
              ? "Try a different title, or switch tabs."
              : "Once you create a role, candidates can apply and Compass starts scoring them automatically."
          }
          action={
            !search && canCreate ? (
              <Link href="/jobs/new" className={buttonClasses("primary", "sm")}>
                Create a job
              </Link>
            ) : undefined
          }
        />
      )}

      {filtered.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2">
          {filtered.map((job) => (
            <JobCard key={job.id} job={job} />
          ))}
        </div>
      )}
    </div>
  );
}
