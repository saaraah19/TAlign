"use client";

import { CompassAsk } from "@/features/compass";
import { LeaveBalanceCard, LeaveRequestForm, MyLeaveRequestsList } from "@/features/leave-requests";

/**
 * Employee-facing leave page — the actual home for a plain `employee`
 * account (NavBar's "Leave" link points here; there is no separate
 * /portal page). CompassAsk sits at the bottom because a leave-balance
 * or policy question is exactly what an employee asks while looking at
 * their balance — Compass routes any EMPLOYEE-role question to
 * knowledge_query regardless of the page (see
 * Compass._resolve_capability_for_role), the same capability as the
 * Knowledge page, surfaced a second place.
 */
export default function PortalLeavePage() {
  return (
    <main className="mx-auto max-w-4xl px-6 py-8 sm:px-8">
      <h1 className="text-2xl font-semibold tracking-tight text-ink">Leave</h1>
      <p className="mt-1 text-sm text-ink/55">
        Request time off and follow each request until it&apos;s decided.
      </p>

      <div className="mt-8 flex flex-col gap-8">
        <LeaveBalanceCard />

        <div className="grid items-start gap-8 lg:grid-cols-2">
          <section>
            <h2 className="mb-3 text-sm font-medium text-ink">Request time off</h2>
            <LeaveRequestForm />
          </section>

          <section>
            <h2 className="mb-3 text-sm font-medium text-ink">Your requests</h2>
            <MyLeaveRequestsList />
          </section>
        </div>

        <CompassAsk />
      </div>
    </main>
  );
}
