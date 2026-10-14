import { formatFileSize } from "@/lib/format-file-size";
import { formatRelativeTime } from "@/lib/format-relative-time";
import type { Resume } from "../types";

/**
 * One previously uploaded resume, as a selectable row. A resume that
 * could not be parsed is shown but disabled: picking it would only
 * lead to a failed analysis, and the candidate is told why.
 */
export function ResumeOption({
  resume,
  selected = false,
  disabled = false,
  onSelect,
}: {
  resume: Resume;
  selected?: boolean;
  disabled?: boolean;
  onSelect: () => void;
}) {
  const unreadable = resume.status === "parse_failed";

  return (
    <button
      type="button"
      onClick={onSelect}
      disabled={disabled || unreadable}
      aria-pressed={selected}
      className={`flex w-full items-center gap-3 rounded-md border px-3.5 py-3 text-left transition-colors disabled:cursor-not-allowed disabled:opacity-60 ${
        selected ? "border-ink ring-1 ring-ink" : "border-line hover:border-ink/30"
      }`}
    >
      <span
        className={`flex h-4 w-4 shrink-0 items-center justify-center rounded-full border ${
          selected ? "border-ink bg-ink" : "border-line"
        }`}
      >
        {selected && <span className="h-1.5 w-1.5 rounded-full bg-white" />}
      </span>
      <span className="min-w-0 flex-1">
        <span className="block truncate text-sm font-medium text-ink">
          {resume.original_filename}
        </span>
        <span className="block text-xs text-ink/45">
          {unreadable ? (
            <span className="text-red-600">Could not be read — try uploading it again</span>
          ) : (
            <>
              {formatFileSize(resume.file_size_bytes)} · Uploaded{" "}
              {formatRelativeTime(resume.created_at)}
            </>
          )}
        </span>
      </span>
    </button>
  );
}
