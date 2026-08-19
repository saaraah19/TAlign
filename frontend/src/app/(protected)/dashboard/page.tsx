"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "@/features/auth";

export default function DashboardPage() {
  const { user, isLoading, logout } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !user) router.replace("/login");
  }, [isLoading, user, router]);

  if (isLoading || !user) {
    return <main className="p-8 text-sm text-gray-500">Loading…</main>;
  }

  return (
    <main className="mx-auto max-w-2xl p-8">
      <h1 className="text-xl font-semibold">Welcome, {user.first_name}</h1>
      <p className="mt-1 text-sm text-gray-500">
        {user.account_type === "candidate"
          ? "Candidate account"
          : `${user.roles.join(", ")} at your company`}
      </p>

      <div className="mt-6 rounded-lg border border-gray-200 p-4 text-sm">
        <p>Email: {user.email}</p>
        <p>Account type: {user.account_type}</p>
        <p>Roles: {user.roles.join(", ") || "none"}</p>
      </div>

      <button
        onClick={() => logout().then(() => router.push("/login"))}
        className="mt-6 rounded-md border border-gray-300 px-4 py-2 text-sm font-medium"
      >
        Sign out
      </button>

      {user.account_type === "internal" && (
        <div className="mt-4 flex gap-4">
          <a href="/jobs" className="text-sm font-medium text-gray-900 underline">
            View jobs →
          </a>
          <a href="/pipeline" className="text-sm font-medium text-gray-900 underline">
            View pipeline →
          </a>
          <a href="/knowledge" className="text-sm font-medium text-gray-900 underline">
            Knowledge Center →
          </a>
        </div>
      )}

      {user.account_type === "candidate" && (
        <div className="mt-4 flex gap-4">
          <a href="/careers" className="text-sm font-medium text-gray-900 underline">
            Browse open jobs →
          </a>
          <a href="/applications" className="text-sm font-medium text-gray-900 underline">
            My applications →
          </a>
        </div>
      )}

      <p className="mt-8 text-xs text-gray-400">
        This is a placeholder — the real Dashboard (Daily Alignment Brief, Quick
        Statistics, AI Recommendations) ships in a later slice. This page exists
        to prove the authentication loop works end to end.
      </p>
    </main>
  );
}
