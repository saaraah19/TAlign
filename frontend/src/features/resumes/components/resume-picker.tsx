"use client";

import { useState } from "react";
import { ApiError } from "@/lib/api-client";
import { useMyResumes, useUploadResume } from "../hooks/use-resumes";
import { ResumeOption } from "./resume-option";
import { ResumeUploadField } from "./resume-upload-field";

/**
 * Pick-and-attach: choosing an existing resume, or uploading a new
 * one, attaches it right away (the application already exists on this
 * screen). The apply form, where no application exists yet, builds on
 * the same two pieces but holds the choice locally until submit.
 */
export function ResumePicker({
  onAttach,
  isAttaching,
}: {
  onAttach: (resumeId: string) => void;
  isAttaching: boolean;
}) {
  const { data: resumes, isLoading } = useMyResumes();
  const uploadResume = useUploadResume();
  const [error, setError] = useState<string | null>(null);

  async function handleFile(file: File) {
    setError(null);
    try {
      const resume = await uploadResume.mutateAsync(file);
      onAttach(resume.id);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Upload failed.");
    }
  }

  const hasResumes = !isLoading && resumes && resumes.length > 0;

  return (
    <div className="flex flex-col gap-5">
      {hasResumes && (
        <div>
          <p className="text-sm font-medium text-ink">Use a resume you&apos;ve already uploaded</p>
          <ul className="mt-2 flex flex-col gap-2">
            {resumes.map((resume) => (
              <li key={resume.id}>
                <ResumeOption
                  resume={resume}
                  disabled={isAttaching}
                  onSelect={() => onAttach(resume.id)}
                />
              </li>
            ))}
          </ul>
        </div>
      )}

      <ResumeUploadField
        label={hasResumes ? "Or upload a new one" : "Upload your resume"}
        isUploading={uploadResume.isPending}
        disabled={uploadResume.isPending || isAttaching}
        error={error}
        onFile={handleFile}
      />
    </div>
  );
}
