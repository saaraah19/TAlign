"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { Card } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import {
  AnalysisProgressIndicator,
  ApplicationStatusBadge,
  ResumeAttachPanel,
  useMyApplications,
} from "@/features/applications";
import { StageJourney } from "@/features/applications/components/workspace/stage-journey";
import { CANDIDATE_APPLICATION_SUGGESTIONS, CompassAsk } from "@/features/compass";
import { formatRelativeTime } from "@/lib/format-relative-time";

export default function MyApplicationDetailPage() {
  const params = useParams<{ id: string }>();
  // Reuse the list query (already cached from the /applications page in
  // the common case) rather than adding a third fetch shape for one field set.
  const { data, isLoading } = useMyApplications();

  if (isLoading) {
    return (
      <main className="mx-auto max-w-4xl px-6 py-8 sm:px-8">
        <Skeleton className="h-8 w-72" />
        <div className="mt-8 grid gap-8 lg:grid-cols-[minmax(0,1fr)_300px]">
          <Skeleton className="h-64 w-full" />
          <Skeleton className="h-56 w-full" />
        </div>
      </main>
    );
  }

  const application = data?.items.find((a) => a.id === params.id);
  if (!application) {
    return (
      <main className="mx-auto max-w-4xl px-6 py-16 sm:px-8">
        <EmptyState
          title="Application not found"
          description="It may have been removed, or the link may be wrong."
          action={
            <Link
              href="/applications"
              className="text-sm font-medium text-ink underline underline-offset-2"
            >
              Back to my applications
            </Link>
          }
        />
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-4xl px-6 py-8 sm:px-8">
      <Link href="/applications" className="text-xs font-medium text-ink/45 hover:text-ink">
        ← My applications
      </Link>

      <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-ink">
            {application.job.title}
          </h1>
          <p className="mt-1 text-sm text-ink/50">
            Applied {formatRelativeTime(application.created_at)}
          </p>
        </div>
        <ApplicationStatusBadge status={application.status} />
      </div>

      <div className="mt-8 grid gap-8 lg:grid-cols-[minmax(0,1fr)_300px]">
        <div className="flex min-w-0 flex-col gap-6">
          <Card className="p-6">
            <h2 className="text-sm font-medium text-ink">Your resume</h2>
            <p className="mt-1 text-xs leading-relaxed text-ink/50">
              This is the resume the company reviews. You can change it any time.
            </p>
            <div className="mt-5">
              <ResumeAttachPanel applicationId={application.id} />
            </div>
            <div className="mt-5">
              <AnalysisProgressIndicator applicationId={application.id} />
            </div>
          </Card>

          <CompassAsk
            applicationId={application.id}
            suggestions={CANDIDATE_APPLICATION_SUGGESTIONS}
            placeholder="Ask about your application…"
          />
        </div>

        <aside>
          <Card className="p-5">
            <p className="mb-4 text-sm font-medium text-ink">Where you are</p>
            <StageJourney status={application.status} audience="candidate" />
          </Card>
        </aside>
      </div>
    </main>
  );
}
