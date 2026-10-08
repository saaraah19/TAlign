"use client";

import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { KanbanBoard } from "@/features/applications";

function PipelineContent() {
  const searchParams = useSearchParams();
  const jobId = searchParams.get("job_id") ?? undefined;

  return (
    <main className="mx-auto max-w-content p-6 sm:p-8">
      <h1 className="text-2xl font-semibold tracking-tight text-ink">Pipeline</h1>
      <p className="mt-1 text-sm text-ink/50">
        {jobId ? "Candidates for this role." : "Every candidate across every open role."}
      </p>

      <div className="mt-7">
        <KanbanBoard initialJobId={jobId} />
      </div>
    </main>
  );
}

export default function PipelinePage() {
  return (
    <Suspense fallback={<main className="p-8 text-sm text-ink/50">Loading…</main>}>
      <PipelineContent />
    </Suspense>
  );
}
