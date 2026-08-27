import Link from "next/link";
import type { LowApplicantJob } from "../types";
import { Section } from "./section";

export function LowApplicantJobsSection({ jobs }: { jobs: LowApplicantJob[] }) {
  return (
    <Section title="Jobs with low applicant volume" empty={jobs.length === 0}>
      <ul className="divide-y divide-gray-200 rounded-lg border border-gray-200">
        {jobs.map((job) => (
          <li key={job.job_id}>
            <Link
              href={`/jobs/${job.job_id}`}
              className="flex flex-col gap-1 px-4 py-3 hover:bg-gray-50 sm:flex-row sm:items-center sm:justify-between sm:gap-0"
            >
              <p className="text-sm font-medium text-gray-900">{job.title}</p>
              <span className="text-xs text-gray-500">
                {job.applicant_count} applicant{job.applicant_count === 1 ? "" : "s"}
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </Section>
  );
}
