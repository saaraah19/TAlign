"use client";

import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { PipelineView } from "@/features/applications";

function PipelineContent() {
  const searchParams = useSearchParams();
  const jobId = searchParams.get("job_id") ?? undefined;

  return (
    <main className="mx-auto max-w-3xl p-6 sm:p-8">
      <h1 className="text-xl font-semibold">Pipeline</h1>
      <p className="mt-1 text-sm text-gray-500">
        {jobId ? "Applications for this job." : "All applications across every open role."}
      </p>

      <div className="mt-6">
        <PipelineView jobId={jobId} />
      </div>
    </main>
  );
}

export default function PipelinePage() {
  return (
    <Suspense fallback={<main className="p-8 text-sm text-gray-500">Loading…</main>}>
      <PipelineContent />
    </Suspense>
  );
}
