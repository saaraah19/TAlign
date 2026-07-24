"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect } from "react";
import {
  AnalysisProgressIndicator,
  ApplicationStatusBadge,
  ResumeAttachPanel,
  useMyApplications,
} from "@/features/applications";
import { useAuth } from "@/features/auth";
import { CompassAsk } from "@/features/compass";

export default function MyApplicationDetailPage() {
  const params = useParams<{ id: string }>();
  const { user, isLoading: authLoading } = useAuth();
  const router = useRouter();
  // Reuse the list query (already cached from the /applications page in
  // the common case) rather than adding a third fetch shape for one field set.
  const { data, isLoading } = useMyApplications();

  useEffect(() => {
    if (!authLoading && !user) router.replace("/login");
  }, [authLoading, user, router]);

  if (authLoading || isLoading || !user) {
    return <main className="p-8 text-sm text-gray-500">Loading…</main>;
  }

  const application = data?.items.find((a) => a.id === params.id);
  if (!application) {
    return <main className="p-8 text-sm text-red-600">Application not found.</main>;
  }

  return (
    <main className="mx-auto max-w-2xl p-8">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">{application.job.title}</h1>
        <ApplicationStatusBadge status={application.status} />
      </div>
      <p className="mt-1 text-sm text-gray-500">
        Applied {new Date(application.created_at).toLocaleDateString()}
      </p>

      <div className="mt-6 flex flex-col gap-6">
        <div>
          <h2 className="text-sm font-medium text-gray-900">Your resume</h2>
          <p className="mt-1 text-xs text-gray-500">
            Attach a resume so this application can be reviewed. You can change it any time.
          </p>
          <div className="mt-3">
            <ResumeAttachPanel applicationId={application.id} />
          </div>
          <div className="mt-3">
            <AnalysisProgressIndicator applicationId={application.id} />
          </div>
        </div>

        <CompassAsk applicationId={application.id} />
      </div>
    </main>
  );
}
