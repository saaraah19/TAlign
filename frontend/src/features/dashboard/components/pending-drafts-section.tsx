import Link from "next/link";
import { EMAIL_TYPE_LABELS, type EmailType } from "@/features/communication";
import type { PendingDraftEmail } from "../types";
import { Section } from "./section";

export function PendingDraftsSection({ drafts }: { drafts: PendingDraftEmail[] }) {
  return (
    <Section title="Draft emails awaiting review" empty={drafts.length === 0}>
      <ul className="divide-y divide-gray-200 rounded-lg border border-gray-200">
        {drafts.map((email) => (
          <li key={email.id}>
            <Link
              href={`/pipeline/${email.application_id}`}
              className="flex flex-col gap-1 px-4 py-3 hover:bg-gray-50 sm:flex-row sm:items-center sm:justify-between sm:gap-0"
            >
              <div>
                <p className="text-sm font-medium text-gray-900">{email.subject}</p>
                <p className="text-xs text-gray-500">To: {email.recipient_email}</p>
              </div>
              <span className="text-xs text-gray-500">
                {EMAIL_TYPE_LABELS[email.email_type as EmailType] ?? email.email_type}
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </Section>
  );
}
