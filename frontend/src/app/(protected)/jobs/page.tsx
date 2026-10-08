"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/features/auth";
import { JobList } from "@/features/jobs";

export default function JobsPage() {
  const { user } = useAuth();
  if (!user) return null; // guaranteed non-null by (protected)/layout.tsx

  const canCreate = user.roles.includes("admin") || user.roles.includes("recruiter");

  return (
    <main className="mx-auto max-w-content p-6 sm:p-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-ink">Jobs</h1>
          <p className="mt-1 text-sm text-ink/50">Manage your open roles.</p>
        </div>
        {canCreate && (
          <Link href="/jobs/new">
            <Button>+ Create job</Button>
          </Link>
        )}
      </div>

      <div className="mt-7">
        <JobList canCreate={canCreate} />
      </div>
    </main>
  );
}
