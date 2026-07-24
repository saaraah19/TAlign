"use client";

import Link from "next/link";
import { useJobs } from "../hooks/use-jobs";
import { EMPLOYMENT_TYPE_LABELS } from "../types";
import { JobStatusBadge } from "./job-status-badge";

export function JobList() {
  const { data, isLoading, error } = useJobs();

  if (isLoading) return <p className="text-sm text-gray-500">Loading jobs…</p>;
  if (error) return <p className="text-sm text-red-600">Could not load jobs.</p>;
  if (!data || data.items.length === 0) {
    return <p className="text-sm text-gray-500">No jobs yet — create your first one.</p>;
  }

  return (
    <ul className="divide-y divide-gray-200 rounded-lg border border-gray-200">
      {data.items.map((job) => (
        <li key={job.id}>
          <Link
            href={`/jobs/${job.id}`}
            className="flex items-center justify-between px-4 py-3 text-sm hover:bg-gray-50"
          >
            <div>
              <p className="font-medium text-gray-900">{job.title}</p>
              <p className="text-gray-500">
                {EMPLOYMENT_TYPE_LABELS[job.employment_type]}
                {job.location ? ` · ${job.location}` : ""}
              </p>
            </div>
            <JobStatusBadge status={job.status} />
          </Link>
        </li>
      ))}
    </ul>
  );
}
