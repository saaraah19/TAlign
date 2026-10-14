"use client";

import { useRouter } from "next/navigation";
import { JobCreateForm } from "@/features/jobs";

export default function NewJobPage() {
  const router = useRouter();

  return (
    <main className="mx-auto max-w-2xl px-6 py-8 sm:px-8">
      <h1 className="text-2xl font-semibold tracking-tight text-ink">New job</h1>
      <p className="mt-1 text-sm text-ink/55">
        Jobs start as a draft — publish when you&apos;re ready to accept applications.
      </p>

      <div className="mt-8">
        <JobCreateForm onSuccess={(jobId) => router.push(`/jobs/${jobId}`)} />
      </div>
    </main>
  );
}
