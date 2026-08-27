"use client";

import { MyApplicationsList } from "@/features/applications";

export default function ApplicationsPage() {
  return (
    <main className="mx-auto max-w-2xl p-6 sm:p-8">
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
