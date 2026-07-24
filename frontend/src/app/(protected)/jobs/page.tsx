"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "@/features/auth";
import { JobList } from "@/features/jobs";

export default function JobsPage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !user) router.replace("/login");
  }, [isLoading, user, router]);

  if (isLoading || !user) return <main className="p-8 text-sm text-gray-500">Loading…</main>;

  const canCreate = user.roles.includes("admin") || user.roles.includes("recruiter");

  return (
    <main className="mx-auto max-w-3xl p-8">
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
