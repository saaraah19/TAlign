"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { useToast } from "@/components/ui/toast";
import { ApiError } from "@/lib/api-client";
import { useDraftEmail, useEmails } from "../hooks/use-communication";
import type { EmailType } from "../types";
import { EmailDraftCard } from "./email-draft-card";

export function CommunicationPanel({
  applicationId,
  isTerminal = false,
}: {
  applicationId: string;
  isTerminal?: boolean;
}) {
  const { data, isLoading } = useEmails(applicationId);
  const draftEmail = useDraftEmail(applicationId);
  const toast = useToast();
  const [error, setError] = useState<string | null>(null);

  async function handleDraft(emailType: EmailType) {
    setError(null);
    try {
      await draftEmail.mutateAsync(emailType);
      toast.success("Draft ready — review it below");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not draft this email.");
    }
  }

  const isEmpty = !isLoading && data && data.items.length === 0;

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <h2 className="text-sm font-medium text-ink">Communication</h2>
        {!isTerminal && (
          <div className="flex flex-wrap gap-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => handleDraft("interview_invitation")}
              disabled={draftEmail.isPending}
            >
              Draft interview invitation
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => handleDraft("rejection")}
              disabled={draftEmail.isPending}
            >
              Draft rejection
            </Button>
          </div>
        )}
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {draftEmail.isPending && (
        <div className="rounded-lg border border-line bg-white p-5">
          <p className="text-sm text-ink/60">Compass is drafting this email…</p>
          <div className="mt-3 flex flex-col gap-2">
            <div className="h-3 w-2/3 animate-pulse rounded bg-ink/[0.06]" />
            <div className="h-3 w-full animate-pulse rounded bg-ink/[0.06]" />
            <div className="h-3 w-5/6 animate-pulse rounded bg-ink/[0.06]" />
          </div>
        </div>
      )}

      {isLoading && <div className="h-24 animate-pulse rounded-lg bg-ink/[0.05]" />}

      {isEmpty && !draftEmail.isPending && (
        <div className="rounded-lg border border-dashed border-line px-5 py-8 text-center">
          <p className="text-sm font-medium text-ink">No emails yet</p>
          <p className="mx-auto mt-1 max-w-sm text-xs leading-relaxed text-ink/50">
            {isTerminal
              ? "This application is closed, so new drafts are turned off."
              : "Draft an interview invitation or a rejection — Compass writes it, you review and edit before anything goes out."}
          </p>
        </div>
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
