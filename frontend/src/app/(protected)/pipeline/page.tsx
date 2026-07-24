"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect } from "react";
import { useAuth } from "@/features/auth";
import { PipelineView } from "@/features/applications";

function PipelineContent() {
  const { user, isLoading } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const jobId = searchParams.get("job_id") ?? undefined;

  useEffect(() => {
    if (!isLoading && !user) router.replace("/login");
  }, [isLoading, user, router]);

  if (isLoading || !user) return <main className="p-8 text-sm text-gray-500">Loading…</main>;

  return (
    <main className="mx-auto max-w-3xl p-8">
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
