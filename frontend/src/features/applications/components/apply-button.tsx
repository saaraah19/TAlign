"use client";

import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/features/auth";

/**
 * Only gets the right person to /careers/{jobId}/apply — the apply and
 * resume steps both happen there together (see ApplyForm) — or explains
 * why they can't yet.
 */
export function ApplyButton({ jobId }: { jobId: string }) {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  if (isLoading) return null;

  if (!user) {
    return (
      <div className="flex flex-col gap-2">
        <Button
          className="w-full"
          onClick={() => router.push(`/register/candidate?next=/careers/${jobId}/apply`)}
        >
          Create an account to apply
        </Button>
        <p className="text-center text-xs text-ink/45">It takes less than a minute.</p>
      </div>
    );
  }

  if (user.account_type !== "candidate") {
    return (
      <p className="text-sm leading-relaxed text-ink/55">
        Only candidate accounts can apply. You&apos;re signed in with a company account.
      </p>
    );
  }

  return (
    <Button className="w-full" onClick={() => router.push(`/careers/${jobId}/apply`)}>
      Apply now
    </Button>
  );
}
