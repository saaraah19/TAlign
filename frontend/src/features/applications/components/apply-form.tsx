"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import {
  ResumeOption,
  ResumeUploadField,
  useMyResumes,
  useUploadResume,
} from "@/features/resumes";
import { ApiError } from "@/lib/api-client";
import { applicationsApi } from "../api";

/**
 * Combined apply + resume flow: one page, one "Submit application" click.
 *
 * Design note: this deliberately does NOT reuse `ResumePicker` — that
 * component attaches immediately on selection, which assumes an
 * Application already exists. Here, resume selection is purely local
 * state until the final submit; a newly uploaded file is uploaded
 * eagerly (to get a resume_id) but not yet attached to anything.
 * `apply()` and `attachResume()` both happen together, only on submit —
 * from the candidate's point of view, one action. The two shared
 * pieces (ResumeOption, ResumeUploadField) keep it looking identical
 * to the picker on the application page.
 */
export function ApplyForm({ jobId }: { jobId: string }) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const toast = useToast();
  const { data: resumes, isLoading: resumesLoading } = useMyResumes();
  const uploadResume = useUploadResume();

  const [selectedResumeId, setSelectedResumeId] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleFile(file: File) {
    setUploadError(null);
    try {
      const resume = await uploadResume.mutateAsync(file);
      setSelectedResumeId(resume.id);
    } catch (err) {
      setUploadError(err instanceof ApiError ? err.message : "Upload failed.");
    }
  }

  async function handleSubmit() {
    if (!selectedResumeId) return;
    setSubmitError(null);
    setIsSubmitting(true);
    try {
      const application = await applicationsApi.apply(jobId);
      await applicationsApi.attachResume(application.id, selectedResumeId);
      queryClient.invalidateQueries({ queryKey: ["applications", "mine"] });
      toast.success("Application submitted");
      router.push(`/applications/${application.id}`);
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setSubmitError("You've already applied to this role — check My applications.");
      } else {
        setSubmitError(
          err instanceof ApiError ? err.message : "Could not submit your application.",
        );
      }
      setIsSubmitting(false);
    }
  }

  const hasResumes = !resumesLoading && resumes && resumes.length > 0;
  const busy = isSubmitting || uploadResume.isPending;

  return (
    <Card className="flex flex-col gap-6 p-6">
      <div>
        <h2 className="text-sm font-medium text-ink">Your resume</h2>
        <p className="mt-1 text-xs leading-relaxed text-ink/50">
          Upload the resume you want this company to review. You can change it later.
        </p>
      </div>

      {resumesLoading && <Skeleton className="h-14 w-full" />}

      {hasResumes && (
        <div>
          <p className="text-sm font-medium text-ink">Use a resume you&apos;ve already uploaded</p>
          <ul className="mt-2 flex flex-col gap-2">
            {resumes.map((resume) => (
              <li key={resume.id}>
                <ResumeOption
                  resume={resume}
                  selected={selectedResumeId === resume.id}
                  disabled={busy}
                  onSelect={() => setSelectedResumeId(resume.id)}
                />
              </li>
            ))}
          </ul>
        </div>
      )}

      <ResumeUploadField
        label={hasResumes ? "Or upload a new resume" : "Upload your resume"}
        isUploading={uploadResume.isPending}
        disabled={busy}
        error={uploadError}
        onFile={handleFile}
      />

      <div className="border-t border-line pt-5">
        {submitError && <p className="mb-3 text-sm text-red-600">{submitError}</p>}
        <Button className="w-full" onClick={handleSubmit} disabled={!selectedResumeId || busy}>
          {isSubmitting ? "Submitting…" : "Submit application"}
        </Button>
        <p className="mt-3 text-center text-xs leading-relaxed text-ink/40">
          An AI reads your resume to help the recruiter review applications faster. Every hiring
          decision is made by a person.
        </p>
      </div>
    </Card>
  );
}
