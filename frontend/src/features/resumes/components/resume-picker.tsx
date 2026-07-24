"use client";

import { useState } from "react";
import { ApiError } from "@/lib/api-client";
import { useMyResumes, useUploadResume } from "../hooks/use-resumes";

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

  async function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setError(null);
    try {
      const resume = await uploadResume.mutateAsync(file);
      onAttach(resume.id);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Upload failed.");
    }
    e.target.value = "";
  }

  return (
    <div className="flex flex-col gap-3">
      {!isLoading && resumes && resumes.length > 0 && (
        <div>
          <p className="text-sm font-medium">Use an existing resume</p>
          <ul className="mt-2 flex flex-col gap-2">
            {resumes.map((resume) => (
              <li key={resume.id}>
                <button
                  onClick={() => onAttach(resume.id)}
                  disabled={isAttaching || resume.status === "parse_failed"}
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-left text-sm disabled:opacity-50"
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
        <p className="text-sm font-medium">
          {resumes && resumes.length > 0 ? "Or upload a new one" : "Upload your resume"}
        </p>
        <input
          type="file"
          accept=".pdf,.docx,.txt"
          onChange={handleFileChange}
          disabled={uploadResume.isPending || isAttaching}
          className="mt-2 text-sm"
        />
        <p className="mt-1 text-xs text-gray-400">PDF, DOCX, or TXT.</p>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}
    </div>
  );
}
