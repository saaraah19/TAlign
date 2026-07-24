"use client";

import { useRouter } from "next/navigation";
import { JobCreateForm } from "@/features/jobs";

export default function NewJobPage() {
  const router = useRouter();

  return (
    <main className="mx-auto max-w-xl p-8">
      <h1 className="text-xl font-semibold">New job</h1>
      <p className="mt-1 text-sm text-gray-500">
        Jobs start as a draft — publish when you're ready to accept applications.
      </p>

      <div className="mt-6">
        <JobCreateForm onSuccess={(jobId) => router.push(`/jobs/${jobId}`)} />
      </div>
    </main>
  );
}
