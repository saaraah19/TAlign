"use client";

import { useAuth } from "@/features/auth";
import { LeaveApprovalQueue } from "@/features/leave-requests";

export default function LeaveRequestsPage() {
  const { user } = useAuth();
  if (!user) return null; // guaranteed non-null by (protected)/layout.tsx

  return (
    <main className="mx-auto max-w-3xl p-6 sm:p-8">
      <h1 className="text-xl font-semibold">Leave requests</h1>
      <p className="mt-1 text-sm text-gray-500">
        Approval routes to any admin or hiring manager — there&apos;s no individual manager
        assignment in this MVP.
      </p>

      <div className="mt-6">
        <LeaveApprovalQueue />
      </div>
    </main>
  );
}
