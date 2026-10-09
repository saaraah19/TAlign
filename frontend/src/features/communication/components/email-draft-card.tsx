"use client";

import { useEffect, useState } from "react";
import { AIMark } from "@/components/ui/ai-mark";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useToast } from "@/components/ui/toast";
import { ApiError } from "@/lib/api-client";
import { useRegenerateEmail, useSendEmail, useUpdateEmail } from "../hooks/use-communication";
import { EMAIL_TYPE_LABELS, type Email } from "../types";

/**
 * An email shown the way a mail client would: header rows (To,
 * Subject) above a message body. While it's a draft the fields are
 * editable in place; once it's marked sent it becomes a read-only
 * preview of exactly what was recorded.
 *
 * Talign does not send real email in the MVP — "Mark as sent" records
 * that the recruiter sent it themselves. The footer says so plainly
 * rather than letting a "Send" button imply otherwise.
 */
export function EmailDraftCard({
  applicationId,
  email,
}: {
  applicationId: string;
  email: Email;
}) {
  const isDraft = email.status === "draft";
  const [subject, setSubject] = useState(email.subject);
  const [body, setBody] = useState(email.body);
  const [error, setError] = useState<string | null>(null);

  // Keep local edit state in sync if the row changes underneath us
  // (e.g. after a regenerate, or the onSettled refetch).
  useEffect(() => {
    setSubject(email.subject);
    setBody(email.body);
  }, [email.subject, email.body]);

  const toast = useToast();
  const regenerate = useRegenerateEmail(applicationId);
  const update = useUpdateEmail(applicationId);
  const send = useSendEmail(applicationId);

  const isBusy = regenerate.isPending || update.isPending || send.isPending;
  const hasUnsavedEdits = isDraft && (subject !== email.subject || body !== email.body);

  async function handleRegenerate() {
    setError(null);
    try {
      await regenerate.mutateAsync(email.id);
      toast.success("Draft regenerated");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not regenerate this draft.");
    }
  }

  async function handleSaveEdits() {
    setError(null);
    try {
      await update.mutateAsync({ emailId: email.id, subject, body });
      toast.success("Edits saved");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not save your edits.");
    }
  }

  async function handleSend() {
    setError(null);
    try {
      // Save any in-progress edits first so nothing typed is lost.
      if (hasUnsavedEdits) {
        await update.mutateAsync({ emailId: email.id, subject, body });
      }
      await send.mutateAsync(email.id);
      toast.success("Email marked as sent");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not mark this email as sent.");
    }
  }

  return (
    <div className="overflow-hidden rounded-lg border border-line bg-white">
      <div className="flex items-center justify-between border-b border-line bg-paper px-4 py-2.5">
        <span className="text-xs font-medium uppercase tracking-wide text-ink/50">
          {EMAIL_TYPE_LABELS[email.email_type]}
        </span>
        {isDraft ? (
          <Badge>Draft</Badge>
        ) : (
          <Badge tone="success">
            Sent {email.sent_at ? new Date(email.sent_at).toLocaleString() : ""}
          </Badge>
        )}
      </div>

      <div className="px-4">
        <div className="flex items-center gap-3 border-b border-line py-2.5 text-sm">
          <span className="w-14 shrink-0 text-xs text-ink/40">To</span>
          <span className="truncate text-ink/80">{email.recipient_email}</span>
        </div>
        <div className="flex items-center gap-3 border-b border-line py-1.5 text-sm">
          <label htmlFor={`subject-${email.id}`} className="w-14 shrink-0 text-xs text-ink/40">
            Subject
          </label>
          {isDraft ? (
            <input
              id={`subject-${email.id}`}
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              disabled={isBusy}
              className="w-full rounded bg-transparent py-1 font-medium text-ink outline-none focus:bg-paper disabled:text-ink/50"
            />
          ) : (
            <span className="py-1 font-medium text-ink">{email.subject}</span>
          )}
        </div>

        <div className="py-3">
          {isDraft ? (
            <>
              <label htmlFor={`body-${email.id}`} className="sr-only">
                Message
              </label>
              <textarea
                id={`body-${email.id}`}
                value={body}
                onChange={(e) => setBody(e.target.value)}
                disabled={isBusy}
                rows={10}
                className="w-full resize-y rounded bg-transparent p-1 text-sm leading-relaxed text-ink/85 outline-none focus:bg-paper disabled:text-ink/50"
              />
            </>
          ) : (
            <p className="whitespace-pre-wrap p-1 text-sm leading-relaxed text-ink/85">
              {email.body}
            </p>
          )}
        </div>
      </div>

      {error && <p className="px-4 pb-2 text-sm text-red-600">{error}</p>}

      {isDraft && (
        <div className="flex flex-wrap items-center gap-2 border-t border-line bg-paper px-4 py-3">
          <Button size="sm" onClick={handleSend} disabled={isBusy}>
            {send.isPending ? "Saving…" : "Mark as sent"}
          </Button>
          {hasUnsavedEdits && (
            <Button size="sm" variant="secondary" onClick={handleSaveEdits} disabled={isBusy}>
              {update.isPending ? "Saving…" : "Save edits"}
            </Button>
          )}
          <Button size="sm" variant="ghost" onClick={handleRegenerate} disabled={isBusy}>
            {regenerate.isPending ? "Regenerating…" : "Regenerate"}
          </Button>
          <p className="w-full text-[11px] text-ink/40 sm:ml-auto sm:w-auto">
            Talign doesn&apos;t send email — send it yourself, then mark it as sent.
          </p>
        </div>
      )}

      <div className="flex items-center gap-1.5 border-t border-line px-4 py-2 text-[11px] text-ink/40">
        {email.llm_provider && email.llm_model ? (
          <>
            <AIMark className="h-3 w-3 text-accent" />
            Drafted by Compass · {email.llm_provider}/{email.llm_model}
          </>
        ) : (
          "Manually edited"
        )}
      </div>
    </div>
  );
}
