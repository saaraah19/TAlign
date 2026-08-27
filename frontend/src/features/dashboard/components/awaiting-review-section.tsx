import Link from "next/link";
import { ApplicationStatusBadge, type ApplicationWithCandidate } from "@/features/applications";
import { Section } from "./section";

export function AwaitingReviewSection({
  applications,
}: {
  applications: ApplicationWithCandidate[];
}) {
  return (
    <Section title="Applications awaiting review" empty={applications.length === 0}>
      <ul className="divide-y divide-gray-200 rounded-lg border border-gray-200">
        {applications.map((application) => (
          <li key={application.id}>
            <Link
              href={`/pipeline/${application.id}`}
              className="flex flex-col gap-1 px-4 py-3 hover:bg-gray-50 sm:flex-row sm:items-center sm:justify-between sm:gap-0"
            >
              <div>
                <p className="text-sm font-medium text-gray-900">
                  {application.candidate.first_name} {application.candidate.last_name}
                </p>
                <p className="text-xs text-gray-500">{application.job.title}</p>
              </div>
              <ApplicationStatusBadge status={application.status} />
            </Link>
          </li>
        ))}
      </ul>
    </Section>
  );
}
