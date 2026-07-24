"use client";

import { useState } from "react";
import { ResumePicker } from "@/features/resumes";
import { ApiError } from "@/lib/api-client";
import { useAttachResume } from "../hooks/use-applications";

export function ResumeAttachPanel({ applicationId }: { applicationId: string }) {
  const attachResume = useAttachResume(applicationId);
  const [error, setError] = useState<string | null>(null);

  async function handleAttach(resumeId: string) {
    setError(null);
    try {
      await attachResume.mutateAsync(resumeId);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not attach resume.");
    }
  }

  return (
    <div>
      <ResumePicker onAttach={handleAttach} isAttaching={attachResume.isPending} />
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
    </div>
  );
}
