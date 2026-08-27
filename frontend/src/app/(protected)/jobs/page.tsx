"use client";

import Link from "next/link";
import { useAuth } from "@/features/auth";
import { JobList } from "@/features/jobs";

export default function JobsPage() {
  const { user } = useAuth();
  if (!user) return null; // guaranteed non-null by (protected)/layout.tsx

  const canCreate = user.roles.includes("admin") || user.roles.includes("recruiter");

  return (
    <main className="mx-auto max-w-3xl p-6 sm:p-8">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Jobs</h1>
        {canCreate && (
          <Link
            href="/jobs/new"
            className="rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white"
          >
            New job
          </Link>
        )}
      </div>

      <div className="mt-6">
        <JobList />
      </div>
    </main>
  );
}
