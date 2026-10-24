import Link from "next/link";
import { Card } from "@/components/ui/card";
import { EMAIL_TYPE_LABELS, type EmailType } from "@/features/communication";
import type { LowApplicantJob, PendingDraftEmail } from "../types";
import type { ApplicationWithCandidate } from "@/features/applications";

export function AttentionNeeded({
  awaitingReview,
  lowApplicantJobs,
  pendingDrafts,
}: {
  awaitingReview: ApplicationWithCandidate[];
  lowApplicantJobs: LowApplicantJob[];
  pendingDrafts: PendingDraftEmail[];
}) {
  const totalCount = awaitingReview.length + lowApplicantJobs.length + pendingDrafts.length;

  return (
    <Card className="p-6">
      <h2 className="text-sm font-medium text-ink">Attention needed</h2>

      {totalCount === 0 ? (
        <div className="mt-4 rounded-md border border-dashed border-line py-8 text-center">
          <p className="text-sm font-medium text-ink">You&apos;re all caught up</p>
          <p className="mt-1 text-xs text-ink/45">Nothing needs your review right now.</p>
        </div>
      ) : (
        <div className="mt-4 flex flex-col gap-5">
          {awaitingReview.length > 0 && (
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-ink/35">
                Applications to review
              </p>
              <ul className="mt-2 flex flex-col gap-1">
                {awaitingReview.slice(0, 4).map((app) => (
                  <li key={app.id}>
                    <Link
                      href={`/pipeline/${app.id}`}
                      className="flex items-center justify-between rounded-md px-2 py-1.5 text-sm hover:bg-ink/[0.03]"
                    >
                      <span className="text-ink">
                        {app.candidate.first_name} {app.candidate.last_name}
                      </span>
                      <span className="text-xs text-ink/40">{app.job.title}</span>
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {lowApplicantJobs.length > 0 && (
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-ink/35">
                Low applicant volume
              </p>
              <ul className="mt-2 flex flex-col gap-1">
                {lowApplicantJobs.slice(0, 3).map((job) => (
                  <li key={job.job_id}>
                    <Link
                      href={`/jobs/${job.job_id}`}
                      className="flex items-center justify-between rounded-md px-2 py-1.5 text-sm hover:bg-ink/[0.03]"
                    >
                      <span className="text-ink">{job.title}</span>
                      <span className="text-xs text-ink/40">
                        {job.applicant_count} applicant{job.applicant_count === 1 ? "" : "s"}
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {pendingDrafts.length > 0 && (
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-ink/35">
                Drafts awaiting review
              </p>
              <ul className="mt-2 flex flex-col gap-1">
                {pendingDrafts.slice(0, 3).map((email) => (
                  <li key={email.id}>
                    <Link
                      href={`/pipeline/${email.application_id}`}
                      className="flex items-center justify-between rounded-md px-2 py-1.5 text-sm hover:bg-ink/[0.03]"
                    >
                      <span className="text-ink">{email.subject}</span>
                      <span className="text-xs text-ink/40">
                        {EMAIL_TYPE_LABELS[email.email_type as EmailType] ?? email.email_type}
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </Card>
  );
}
