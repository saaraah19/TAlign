"use client";

import { useRouter } from "next/navigation";
import { useRouteId } from "@/lib/route-id";
import { JobDetail } from "@/features/jobs";

export default function JobDetailPage() {
  const id = useRouteId();
  const router = useRouter();

  return (
    <main className="mx-auto max-w-3xl px-6 py-8 sm:px-8">
      <JobDetail jobId={id} onDeleted={() => router.push("/jobs")} />
    </main>
  );
}
