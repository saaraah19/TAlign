"use client";

import { useEffect, useState } from "react";
import { ApiError } from "@/lib/api-client";
import {
  useRegenerateEmail,
  useSendEmail,
  useUpdateEmail,
} from "../hooks/use-communication";
import { EMAIL_TYPE_LABELS, type Email } from "../types";

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

  const regenerate = useRegenerateEmail(applicationId);
  const update = useUpdateEmail(applicationId);
  const send = useSendEmail(applicationId);

  const isBusy = regenerate.isPending || update.isPending || send.isPending;
  const hasUnsavedEdits = isDraft && (subject !== email.subject || body !== email.body);

  async function handleRegenerate() {
    setError(null);
    try {
      await regenerate.mutateAsync(email.id);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not regenerate this draft.");
    }
  }

  async function handleSaveEdits() {
    setError(null);
    try {
      await update.mutateAsync({ emailId: email.id, subject, body });
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
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not mark this email as sent.");
    }
  }

  return (
    <div className="rounded-lg border border-gray-200 p-4">
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <span className="text-xs font-medium uppercase tracking-wide text-gray-500">
          {EMAIL_TYPE_LABELS[email.email_type]}
        </span>
        {isDraft ? (
          <span className="rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-700">
            Draft
          </span>
        ) : (
          <span className="rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-700">
            Sent {email.sent_at ? new Date(email.sent_at).toLocaleString() : ""}
          </span>
        )}
      </div>

      <p className="mt-2 text-xs text-gray-500">To: {email.recipient_email}</p>

      <div className="mt-3">
        <label className="block text-xs font-medium text-gray-500">Subject</label>
        <input
          value={subject}
          onChange={(e) => setSubject(e.target.value)}
          disabled={!isDraft || isBusy}
          className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm disabled:bg-gray-50 disabled:text-gray-500"
        />
      </div>

      <div className="mt-3">
        <label className="block text-xs font-medium text-gray-500">Body</label>
        <textarea
          value={body}
          onChange={(e) => setBody(e.target.value)}
          disabled={!isDraft || isBusy}
          rows={8}
          className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm disabled:bg-gray-50 disabled:text-gray-500"
        />
      </div>

      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}

      {isDraft && (
        <div className="mt-3 flex flex-wrap gap-2">
          <button
            onClick={handleSend}
            disabled={isBusy}
            className="rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
          >
            {send.isPending ? "Sending…" : "Mark as sent"}
          </button>
          {hasUnsavedEdits && (
            <button
              onClick={handleSaveEdits}
              disabled={isBusy}
              className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium disabled:opacity-50"
            >
              {update.isPending ? "Saving…" : "Save edits"}
            </button>
          )}
          <button
            onClick={handleRegenerate}
            disabled={isBusy}
            className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium disabled:opacity-50"
          >
            {regenerate.isPending ? "Regenerating…" : "Regenerate"}
          </button>
        </div>
      )}

      <p className="mt-3 text-xs text-gray-400">
        {email.llm_provider && email.llm_model
          ? `Drafted by ${email.llm_provider}/${email.llm_model}`
          : "Manually edited"}
      </p>
    </div>
  );
}
