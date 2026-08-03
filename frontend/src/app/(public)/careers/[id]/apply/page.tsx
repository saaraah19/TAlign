"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect } from "react";
import { ApplyForm } from "@/features/applications";
import { useAuth } from "@/features/auth";
import { EMPLOYMENT_TYPE_LABELS, usePublicJob } from "@/features/jobs";

export default function ApplyToJobPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const { user, isLoading: authLoading } = useAuth();
  const { data: job, isLoading: jobLoading, error: jobError } = usePublicJob(params.id);

  useEffect(() => {
    if (!authLoading && !user) {
      router.replace(`/register/candidate?next=/careers/${params.id}/apply`);
    }
  }, [authLoading, user, router, params.id]);

  if (authLoading || !user) return <main className="p-8 text-sm text-gray-500">Loading…</main>;

  if (user.account_type !== "candidate") {
    return (
      <main className="p-8 text-sm text-gray-500">
        Only candidate accounts can apply. You&apos;re signed in as an internal user.
      </main>
    );
  }

  if (jobLoading) return <main className="p-8 text-sm text-gray-500">Loading…</main>;
  if (jobError || !job) {
    return (
      <main className="p-8 text-sm text-red-600">
        This job is no longer accepting applications, or doesn&apos;t exist.
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-2xl p-8">
      <Link href={`/careers/${job.id}`} className="text-xs text-gray-400 underline">
        ← Back to job
      </Link>

      <h1 className="mt-2 text-xl font-semibold">Apply to {job.title}</h1>
      <p className="mt-1 text-sm text-gray-500">
        {EMPLOYMENT_TYPE_LABELS[job.employment_type]}
        {job.location ? ` · ${job.location}` : ""}
      </p>

      <div className="mt-6">
        <ApplyForm jobId={job.id} />
      </div>
    </main>
  );
}
