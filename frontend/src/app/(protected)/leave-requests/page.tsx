"use client";

import { useAuth } from "@/features/auth";
import { LeaveApprovalQueue } from "@/features/leave-requests";

export default function LeaveRequestsPage() {
  const { user } = useAuth();
  if (!user) return null; // guaranteed non-null by (protected)/layout.tsx

  return (
    <main className="mx-auto max-w-4xl px-6 py-8 sm:px-8">
      <h1 className="text-2xl font-semibold tracking-tight text-ink">Leave requests</h1>
      <p className="mt-1 text-sm text-ink/55">
        Any admin or hiring manager can review these — there&apos;s no individual manager
        assignment in this MVP.
      </p>

      <div className="mt-8">
        <LeaveApprovalQueue />
      </div>
    </main>
  );
}
