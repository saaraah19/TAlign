"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { Avatar } from "@/components/ui/avatar";
import { formatRelativeTime } from "@/lib/format-relative-time";
import type { ApplicationWithCandidate } from "../../types";
import { ApplicationStatusBadge } from "../application-status-badge";

export function CandidateHeader({ application }: { application: ApplicationWithCandidate }) {
  const router = useRouter();
  const { candidate, job } = application;

  return (
    <header>
      <button
        onClick={() => router.back()}
        className="text-xs font-medium text-ink/45 transition-colors hover:text-ink"
      >
        ← Back
      </button>

      <div className="mt-4 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-4">
          <Avatar firstName={candidate.first_name} lastName={candidate.last_name} size={52} />
          <div className="min-w-0">
            <h1 className="truncate text-2xl font-semibold tracking-tight text-ink">
              {candidate.first_name} {candidate.last_name}
            </h1>
            <p className="mt-0.5 truncate text-sm text-ink/55">
              {candidate.email} ·{" "}
              <Link href={`/jobs/${job.id}`} className="underline-offset-2 hover:underline">
                {job.title}
              </Link>
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-ink/40">
            Applied {formatRelativeTime(application.created_at)}
          </span>
          <ApplicationStatusBadge status={application.status} />
        </div>
      </div>
    </header>
  );
}
