"use client";

import { useParams, useRouter } from "next/navigation";
import { JobDetail } from "@/features/jobs";

export default function JobDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();

  return (
    <main className="mx-auto max-w-2xl p-8">
      <JobDetail jobId={params.id} onDeleted={() => router.push("/jobs")} />
    </main>
  );
}
