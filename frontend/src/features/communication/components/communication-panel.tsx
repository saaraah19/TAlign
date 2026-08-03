"use client";

import { useState } from "react";
import { ApiError } from "@/lib/api-client";
import { useDraftEmail, useEmails } from "../hooks/use-communication";
import type { EmailType } from "../types";
import { EmailDraftCard } from "./email-draft-card";

export function CommunicationPanel({ applicationId }: { applicationId: string }) {
  const { data, isLoading } = useEmails(applicationId);
  const draftEmail = useDraftEmail(applicationId);
  const [error, setError] = useState<string | null>(null);

  async function handleDraft(emailType: EmailType) {
    setError(null);
    try {
      await draftEmail.mutateAsync(emailType);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not draft this email.");
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-medium text-gray-900">Communication</h2>
        <div className="flex gap-2">
          <button
            onClick={() => handleDraft("interview_invitation")}
            disabled={draftEmail.isPending}
            className="rounded-md border border-gray-300 px-3 py-1.5 text-xs font-medium disabled:opacity-50"
          >
            Draft interview invitation
          </button>
          <button
            onClick={() => handleDraft("rejection")}
            disabled={draftEmail.isPending}
            className="rounded-md border border-gray-300 px-3 py-1.5 text-xs font-medium disabled:opacity-50"
          >
            Draft rejection
          </button>
        </div>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}
      {draftEmail.isPending && <p className="text-sm text-gray-500">Drafting…</p>}

      {isLoading && <p className="text-sm text-gray-500">Loading…</p>}
      {!isLoading && data && data.items.length === 0 && (
        <p className="text-sm text-gray-500">No emails drafted yet for this application.</p>
      )}
      {data && data.items.length > 0 && (
        <div className="flex flex-col gap-4">
          {data.items.map((email) => (
            <EmailDraftCard key={email.id} applicationId={applicationId} email={email} />
          ))}
        </div>
      )}
    </div>
  );
}
