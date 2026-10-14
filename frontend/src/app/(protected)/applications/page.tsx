"use client";

import { MyApplicationsList } from "@/features/applications";

export default function ApplicationsPage() {
  return (
    <main className="mx-auto max-w-4xl px-6 py-8 sm:px-8">
      <h1 className="text-2xl font-semibold tracking-tight text-ink">My applications</h1>
      <p className="mt-1 text-sm text-ink/55">
        Follow every role you&apos;ve applied to, from submission to decision.
      </p>

      <div className="mt-8">
        <MyApplicationsList />
      </div>
    </main>
  );
}
