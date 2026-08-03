"use client";

import { useRouter } from "next/navigation";
import { useAuth } from "@/features/auth";

/**
 * No longer applies inline — the actual apply + resume submission both
 * happen together on /careers/{jobId}/apply (see ApplyForm). This
 * button's only job now is getting the right person to that page, or
 * explaining why they can't get there yet.
 */
export function ApplyButton({ jobId }: { jobId: string }) {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  if (isLoading) return null;

  if (!user) {
    return (
      <button
        onClick={() => router.push(`/register/candidate?next=/careers/${jobId}/apply`)}
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

  return (
    <button
      onClick={() => router.push(`/careers/${jobId}/apply`)}
      className="rounded-md bg-gray-900 px-5 py-2.5 text-sm font-medium text-white"
    >
      Apply now
    </button>
  );
}
