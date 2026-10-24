"use client";

import Link from "next/link";
import { useRouteId } from "@/lib/route-id";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { ApplyButton } from "@/features/applications";
import {
  EMPLOYMENT_TYPE_LABELS,
  formatSalaryRange,
  SkillChips,
  usePublicJob,
} from "@/features/jobs";
import { formatRelativeTime } from "@/lib/format-relative-time";

export default function PublicJobDetailPage() {
  const id = useRouteId();
  const { data: job, isLoading, error } = usePublicJob(id);

  if (isLoading) {
    return (
      <main className="mx-auto max-w-content px-6 py-10 sm:px-8">
        <Skeleton className="h-8 w-72" />
        <div className="mt-8 grid gap-8 lg:grid-cols-[minmax(0,1fr)_320px]">
          <Skeleton className="h-64 w-full" />
          <Skeleton className="h-56 w-full" />
        </div>
      </main>
    );
  }

  if (error || !job) {
    return (
      <main className="mx-auto max-w-2xl px-6 py-16 sm:px-8">
        <EmptyState
          title="This position isn't available"
          description="It may have been filled or closed, or the link may be wrong."
          action={
            <Link
              href="/careers"
              className="text-sm font-medium text-ink underline underline-offset-2"
            >
              Browse open positions
            </Link>
          }
        />
      </main>
    );
  }

  const salary = formatSalaryRange(job);

  return (
    <main className="mx-auto max-w-content px-6 py-10 sm:px-8">
      <Link href="/careers" className="text-xs font-medium text-ink/45 hover:text-ink">
        ← All open positions
      </Link>

      <div className="mt-6 grid gap-8 lg:grid-cols-[minmax(0,1fr)_320px]">
        <article className="min-w-0">
          <h1 className="text-3xl font-semibold tracking-tight text-ink">{job.title}</h1>
          <p className="mt-1.5 text-lg text-ink/60">{job.company_name}</p>
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <Badge>{EMPLOYMENT_TYPE_LABELS[job.employment_type]}</Badge>
            {job.location && <Badge>{job.location}</Badge>}
            <span className="text-xs text-ink/40">Posted {formatRelativeTime(job.created_at)}</span>
          </div>

          <div className="mt-8 rounded-lg border border-line bg-white p-6">
            <h2 className="text-sm font-medium text-ink">About the role</h2>
            <p className="mt-3 whitespace-pre-wrap text-sm leading-relaxed text-ink/70">
              {job.description}
            </p>
          </div>
        </article>

        <aside className="lg:sticky lg:top-24 lg:self-start">
          <Card className="flex flex-col gap-5 p-5">
            {salary && (
              <div>
                <p className="text-xs text-ink/40">Salary</p>
                <p className="mt-0.5 text-sm font-medium text-ink">{salary}</p>
              </div>
            )}
            {job.min_years_experience !== null && (
              <div>
                <p className="text-xs text-ink/40">Experience</p>
                <p className="mt-0.5 text-sm font-medium text-ink">
                  {job.min_years_experience}+ {job.min_years_experience === 1 ? "year" : "years"}
                </p>
              </div>
            )}
            {job.required_skills.length > 0 && (
              <div>
                <p className="text-xs text-ink/40">Required skills</p>
                <SkillChips skills={job.required_skills} className="mt-2" />
              </div>
            )}
            {job.preferred_skills.length > 0 && (
              <div>
                <p className="text-xs text-ink/40">Nice to have</p>
                <SkillChips skills={job.preferred_skills} className="mt-2" />
              </div>
            )}
            <div className="border-t border-line pt-5">
              <ApplyButton jobId={job.id} />
            </div>
          </Card>
        </aside>
      </div>
    </main>
  );
}
