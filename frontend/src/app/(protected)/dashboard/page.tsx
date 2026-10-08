"use client";

import Link from "next/link";
import { Card } from "@/components/ui/card";
import { useAuth } from "@/features/auth";
import { DashboardView } from "@/features/dashboard";
import { isPlainEmployee } from "@/lib/roles";

export default function DashboardPage() {
  const { user } = useAuth();
  if (!user) return null; // guaranteed non-null by (protected)/layout.tsx; guards TypeScript only

  // `account_type === "internal"` also covers hired employees, so the
  // recruiter Dashboard must be gated on roles, not account_type — its
  // API (GET /dashboard) is recruiter-only and would 403 for an employee.
  const plainEmployee = isPlainEmployee(user.roles);
  const showRecruiterDashboard = user.account_type === "internal" && !plainEmployee;

  if (showRecruiterDashboard) {
    return (
      <main className="mx-auto max-w-content p-6 sm:p-8">
        <DashboardView />
      </main>
    );
  }

  // Employee and candidate homes are deliberately simple -- neither
  // role has "attention needed" recruiting data, so they get a short
  // welcome plus direct links, styled with the same design tokens
  // rather than the full recruiter workspace.
  return (
    <main className="mx-auto max-w-2xl p-6 sm:p-8">
      <h1 className="text-2xl font-semibold tracking-tight text-ink">
        Welcome, {user.first_name}.
      </h1>
      <p className="mt-1 text-sm text-ink/50">
        {user.account_type === "candidate" ? "Candidate account" : "Employee at your company"}
      </p>

      <div className="mt-8 grid gap-4 sm:grid-cols-2">
        {plainEmployee && (
          <>
            <Card className="p-5">
              <Link href="/portal/leave" className="flex flex-col gap-1">
                <span className="text-sm font-medium text-ink">Request leave →</span>
                <span className="text-xs text-ink/45">Check your balance or submit a request.</span>
              </Link>
            </Card>
            <Card className="p-5">
              <Link href="/knowledge" className="flex flex-col gap-1">
                <span className="text-sm font-medium text-ink">Company knowledge →</span>
                <span className="text-xs text-ink/45">Ask Compass about policies and benefits.</span>
              </Link>
            </Card>
          </>
        )}

        {user.account_type === "candidate" && (
          <>
            <Card className="p-5">
              <a href="/careers" className="flex flex-col gap-1">
                <span className="text-sm font-medium text-ink">Browse open jobs →</span>
                <span className="text-xs text-ink/45">See every role currently hiring.</span>
              </a>
            </Card>
            <Card className="p-5">
              <a href="/applications" className="flex flex-col gap-1">
                <span className="text-sm font-medium text-ink">My applications →</span>
                <span className="text-xs text-ink/45">Track status and attach your resume.</span>
              </a>
            </Card>
          </>
        )}
      </div>
    </main>
  );
}
