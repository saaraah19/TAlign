"use client";

import Link from "next/link";
import { useMyApplications } from "../hooks/use-applications";
import { ApplicationStatusBadge } from "./application-status-badge";

export function MyApplicationsList() {
  const { data, isLoading, error } = useMyApplications();

  if (isLoading) return <p className="text-sm text-gray-500">Loading your applications…</p>;
  if (error) return <p className="text-sm text-red-600">Could not load your applications.</p>;
  if (!data || data.items.length === 0) {
    return (
      <p className="text-sm text-gray-500">
        You haven&apos;t applied to any jobs yet — browse open positions on{" "}
        <a href="/careers" className="underline">
          Careers
        </a>
        .
      </p>
    );
  }

  return (
    <ul className="divide-y divide-gray-200 rounded-lg border border-gray-200">
      {data.items.map((application) => (
        <li key={application.id}>
          <Link
            href={`/applications/${application.id}`}
            className="flex flex-col gap-1 px-4 py-3 text-sm hover:bg-gray-50 sm:flex-row sm:items-center sm:justify-between sm:gap-0"
          >
            <div>
              <p className="font-medium text-gray-900">{application.job.title}</p>
              <p className="text-gray-500">
                Applied {new Date(application.created_at).toLocaleDateString()}
              </p>
            </div>
            <ApplicationStatusBadge status={application.status} />
          </Link>
        </li>
      ))}
    </ul>
  );
}
