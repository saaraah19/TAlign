"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "@/features/auth";
import { MyApplicationsList } from "@/features/applications";

export default function ApplicationsPage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !user) router.replace("/login");
  }, [isLoading, user, router]);

  if (isLoading || !user) return <main className="p-8 text-sm text-gray-500">Loading…</main>;

  return (
    <main className="mx-auto max-w-2xl p-8">
      <h1 className="text-xl font-semibold">My applications</h1>
      <p className="mt-1 text-sm text-gray-500">
        Track the status of every job you&apos;ve applied to.
      </p>

      <div className="mt-6">
        <MyApplicationsList />
      </div>
    </main>
  );
}
