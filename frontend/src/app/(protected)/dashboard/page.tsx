"use client";

import Link from "next/link";
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

  return (
    <main className="mx-auto max-w-4xl p-6 sm:p-8">
      <h1 className="text-xl font-semibold">Welcome, {user.first_name}</h1>
      <p className="mt-1 text-sm text-gray-500">
        {user.account_type === "candidate"
          ? "Candidate account"
          : `${user.roles.join(", ")} at your company`}
      </p>

      {showRecruiterDashboard && (
        <div className="mt-8">
          <DashboardView />
        </div>
      )}

      {plainEmployee && (
        <div className="mt-6 flex flex-wrap gap-4">
          <Link href="/portal/leave" className="text-sm font-medium text-gray-900 underline">
            Request leave →
          </Link>
          <Link href="/knowledge" className="text-sm font-medium text-gray-900 underline">
            Company knowledge &amp; Compass →
          </Link>
        </div>
      )}

      {user.account_type === "candidate" && (
        <div className="mt-6 flex flex-wrap gap-4">
          <a href="/careers" className="text-sm font-medium text-gray-900 underline">
            Browse open jobs →
          </a>
          <a href="/applications" className="text-sm font-medium text-gray-900 underline">
            My applications →
          </a>
        </div>
      )}
    </main>
  );
}
