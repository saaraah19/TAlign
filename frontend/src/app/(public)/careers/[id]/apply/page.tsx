"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect } from "react";
import { EmptyState } from "@/components/ui/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { ApplyForm } from "@/features/applications";
import { useAuth } from "@/features/auth";
import { EMPLOYMENT_TYPE_LABELS, usePublicJob } from "@/features/jobs";

function PageSkeleton() {
  return (
    <main className="mx-auto max-w-2xl px-6 py-10 sm:px-8">
      <Skeleton className="h-8 w-64" />
      <Skeleton className="mt-8 h-64 w-full" />
    </main>
  );
}

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

  if (authLoading || !user) return <PageSkeleton />;

  if (user.account_type !== "candidate") {
    return (
      <main className="mx-auto max-w-2xl px-6 py-16 sm:px-8">
        <EmptyState
          title="Only candidate accounts can apply"
          description="You're signed in with a company account. Use a candidate account to apply to roles."
        />
      </main>
    );
  }

  if (jobLoading) return <PageSkeleton />;

  if (jobError || !job) {
    return (
      <main className="mx-auto max-w-2xl px-6 py-16 sm:px-8">
        <EmptyState
          title="This position isn't available"
          description="It may have been filled or closed, or the link may be wrong."
          action={
            <Link
              href="/careers"
              className="text-sm font-medium text-ink underline underline-offset-2"
            >
              Browse open positions
            </Link>
          }
        />
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-2xl px-6 py-10 sm:px-8">
      <Link href={`/careers/${job.id}`} className="text-xs font-medium text-ink/45 hover:text-ink">
        ← Back to the role
      </Link>

      <h1 className="mt-4 text-2xl font-semibold tracking-tight text-ink">
        Apply to {job.title}
      </h1>
      <p className="mt-1 text-sm text-ink/55">
        {job.company_name} · {EMPLOYMENT_TYPE_LABELS[job.employment_type]}
        {job.location ? ` · ${job.location}` : ""}
      </p>

      <div className="mt-8">
        <ApplyForm jobId={job.id} />
      </div>
    </main>
  );
}
