"use client";

import { useId } from "react";

/**
 * The file chooser for resumes, shared by the apply form and the
 * "attach a resume" panel so both look and behave the same. A dashed
 * drop-style target (clickable, keyboard-reachable through the hidden
 * input's focus ring on the label) instead of the browser's default
 * file button.
 */
export function ResumeUploadField({
  label,
  isUploading,
  disabled,
  error,
  onFile,
}: {
  label: string;
  isUploading: boolean;
  disabled: boolean;
  error: string | null;
  onFile: (file: File) => void;
}) {
  const inputId = useId();

  return (
    <div>
      <p className="text-sm font-medium text-ink">{label}</p>
      <label
        htmlFor={inputId}
        className={`mt-2 flex items-center justify-between gap-3 rounded-md border border-dashed border-line px-4 py-3.5 text-sm transition-colors focus-within:ring-2 focus-within:ring-accent/30 ${
          disabled ? "cursor-not-allowed opacity-60" : "cursor-pointer hover:border-ink/30"
        }`}
      >
        <span className="flex items-center gap-2.5 text-ink/60">
          {isUploading ? (
            <>
              <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-line border-t-ink" />
              Uploading…
            </>
          ) : (
            "Choose a PDF, DOCX or TXT file"
          )}
        </span>
        <span className="shrink-0 text-xs text-ink/40">Up to 5 MB</span>
        <input
          id={inputId}
          type="file"
          accept=".pdf,.docx,.txt"
          disabled={disabled}
          className="sr-only"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) onFile(file);
            // Reset so choosing the same file again still fires onChange.
            e.target.value = "";
          }}
        />
      </label>
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
    </div>
  );
}
