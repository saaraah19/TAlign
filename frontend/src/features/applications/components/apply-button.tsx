"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { useAuth } from "@/features/auth";
import { ApiError } from "@/lib/api-client";
import { useApplyToJob } from "../hooks/use-applications";

export function ApplyButton({ jobId }: { jobId: string }) {
  const { user, isLoading } = useAuth();
  const router = useRouter();
  const applyToJob = useApplyToJob();
  const [error, setError] = useState<string | null>(null);
  const [applied, setApplied] = useState(false);

  if (isLoading) return null;

  if (!user) {
    return (
      <button
        onClick={() => router.push(`/register/candidate?next=/careers/${jobId}`)}
        className="rounded-md bg-gray-900 px-5 py-2.5 text-sm font-medium text-white"
      >
        Sign in to apply
      </button>
    );
  }

  if (user.account_type !== "candidate") {
    return (
      <p className="text-sm text-gray-500">
        Only candidate accounts can apply. You&apos;re signed in as an internal user.
      </p>
    );
  }

  if (applied) {
    return <p className="text-sm font-medium text-green-700">Application submitted ✓</p>;
  }

  async function handleApply() {
    setError(null);
    try {
      await applyToJob.mutateAsync(jobId);
      setApplied(true);
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setError("You've already applied to this job.");
      } else {
        setError(err instanceof ApiError ? err.message : "Could not submit your application.");
      }
    }
  }

  return (
    <div>
      <button
        onClick={handleApply}
        disabled={applyToJob.isPending}
        className="rounded-md bg-gray-900 px-5 py-2.5 text-sm font-medium text-white disabled:opacity-50"
      >
        {applyToJob.isPending ? "Submitting…" : "Apply now"}
      </button>
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
    </div>
  );
}
