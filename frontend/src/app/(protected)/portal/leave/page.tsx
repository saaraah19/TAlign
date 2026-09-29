"use client";

import { CompassAsk } from "@/features/compass";
import { LeaveBalanceCard, LeaveRequestForm, MyLeaveRequestsList } from "@/features/leave-requests";

/**
 * Employee-facing leave page — confirmed to be the actual home for a
 * plain `employee`-role account: there is no separate `/portal` page
 * anywhere in this repo (checked directly), so this is not a stopgap
 * anymore, it's genuinely where NavBar's "Leave" link for employees
 * points. CompassAsk is included here (rather than only on /knowledge)
 * because a leave-balance/policy question is exactly the kind of thing
 * an employee would ask right where they're already looking at their
 * balance — Compass.handle_message routes any EMPLOYEE-role question
 * straight to knowledge_query regardless of what page it's asked from
 * (see Compass._resolve_capability_for_role), so this is the same
 * capability as the Knowledge page's, just surfaced a second place.
 */
export default function PortalLeavePage() {
  return (
    <main className="mx-auto max-w-2xl p-6 sm:p-8">
      <h1 className="text-xl font-semibold">Leave</h1>

      <div className="mt-6">
        <LeaveBalanceCard />
      </div>

      <div className="mt-8">
        <h2 className="text-sm font-medium text-gray-900">Request time off</h2>
        <div className="mt-3">
          <LeaveRequestForm />
        </div>
      </div>

      <div className="mt-8">
        <h2 className="text-sm font-medium text-gray-900">Your requests</h2>
        <div className="mt-3">
          <MyLeaveRequestsList />
        </div>
      </div>

      <div className="mt-8">
        <h2 className="text-sm font-medium text-gray-900">Ask Compass</h2>
        <div className="mt-3">
          <CompassAsk />
        </div>
      </div>
    </main>
  );
}
