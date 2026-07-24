"use client";

import { useParams } from "next/navigation";
import { ApplyButton } from "@/features/applications";
import { EMPLOYMENT_TYPE_LABELS, usePublicJob } from "@/features/jobs";

export default function PublicJobDetailPage() {
  const params = useParams<{ id: string }>();
  const { data: job, isLoading, error } = usePublicJob(params.id);

  if (isLoading) return <main className="p-8 text-sm text-gray-500">Loading…</main>;
  if (error || !job) {
    return (
      <main className="p-8 text-sm text-red-600">
        This job is no longer accepting applications, or doesn&apos;t exist.
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-2xl p-8">
      <h1 className="text-xl font-semibold">{job.title}</h1>
      <p className="mt-1 text-sm text-gray-500">
        {EMPLOYMENT_TYPE_LABELS[job.employment_type]}
        {job.location ? ` · ${job.location}` : ""}
        {job.salary_min || job.salary_max
          ? ` · $${job.salary_min ?? "?"} – $${job.salary_max ?? "?"}`
          : ""}
      </p>

      <p className="mt-6 whitespace-pre-wrap text-sm text-gray-700">{job.description}</p>

      <div className="mt-8">
        <ApplyButton jobId={job.id} />
      </div>
    </main>
  );
}
