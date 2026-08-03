"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useMyResumes, useUploadResume } from "@/features/resumes";
import { ApiError } from "@/lib/api-client";
import { applicationsApi } from "../api";

/**
 * Combined apply + resume flow: one page, one "Submit application" click.
 *
 * Design note: this deliberately does NOT reuse `ResumePicker` — that
 * component fires `attachResume` immediately on selection, which
 * assumes an Application already exists. Here, resume selection is
 * purely local state until the final submit; nothing hits the network
 * for an existing-resume pick, and a newly uploaded file is uploaded
 * eagerly (to get a resume_id) but not yet attached to anything.
 * `apply()` and `attachResume()` both happen together, only on submit —
 * from the candidate's point of view, one action.
 */
export function ApplyForm({ jobId }: { jobId: string }) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { data: resumes, isLoading: resumesLoading } = useMyResumes();
  const uploadResume = useUploadResume();

  const [selectedResumeId, setSelectedResumeId] = useState<string | null>(null);
  const [selectedFilename, setSelectedFilename] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadError(null);
    try {
      const resume = await uploadResume.mutateAsync(file);
      setSelectedResumeId(resume.id);
      setSelectedFilename(resume.original_filename);
    } catch (err) {
      setUploadError(err instanceof ApiError ? err.message : "Upload failed.");
    }
    e.target.value = "";
  }

  async function handleSubmit() {
    if (!selectedResumeId) return;
    setSubmitError(null);
    setIsSubmitting(true);
    try {
      const application = await applicationsApi.apply(jobId);
      await applicationsApi.attachResume(application.id, selectedResumeId);
      queryClient.invalidateQueries({ queryKey: ["applications", "mine"] });
      router.push(`/applications/${application.id}`);
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setSubmitError("You've already applied to this job — check My Applications.");
      } else {
        setSubmitError(err instanceof ApiError ? err.message : "Could not submit your application.");
      }
      setIsSubmitting(false);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      {!resumesLoading && resumes && resumes.length > 0 && (
        <div>
          <p className="text-sm font-medium text-gray-900">Use an existing resume</p>
          <ul className="mt-2 flex flex-col gap-2">
            {resumes.map((resume) => (
              <li key={resume.id}>
                <button
                  type="button"
                  onClick={() => {
                    setSelectedResumeId(resume.id);
                    setSelectedFilename(resume.original_filename);
                  }}
                  disabled={resume.status === "parse_failed"}
                  className={`w-full rounded-md border px-3 py-2 text-left text-sm disabled:opacity-50 ${
                    selectedResumeId === resume.id
                      ? "border-gray-900 ring-1 ring-gray-900"
                      : "border-gray-300"
                  }`}
                >
                  {resume.original_filename}
                  {resume.status === "parse_failed" && (
                    <span className="ml-2 text-xs text-red-600">Could not be read</span>
                  )}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div>
        <p className="text-sm font-medium text-gray-900">
          {resumes && resumes.length > 0 ? "Or upload a new resume" : "Upload your resume"}
        </p>
        <input
          type="file"
          accept=".pdf,.docx,.txt"
          onChange={handleFileChange}
          disabled={uploadResume.isPending || isSubmitting}
          className="mt-2 text-sm"
        />
        <p className="mt-1 text-xs text-gray-400">PDF, DOCX, or TXT.</p>
        {uploadResume.isPending && <p className="mt-1 text-xs text-gray-500">Uploading…</p>}
        {uploadError && <p className="mt-1 text-sm text-red-600">{uploadError}</p>}
      </div>

      {selectedResumeId && selectedFilename && (
        <p className="text-sm text-green-700">Selected: {selectedFilename}</p>
      )}

      {submitError && <p className="text-sm text-red-600">{submitError}</p>}

      <button
        type="button"
        onClick={handleSubmit}
        disabled={!selectedResumeId || isSubmitting || uploadResume.isPending}
        className="mt-2 rounded-md bg-gray-900 px-5 py-2.5 text-sm font-medium text-white disabled:opacity-50"
      >
        {isSubmitting ? "Submitting…" : "Submit application"}
      </button>
    </div>
  );
}
