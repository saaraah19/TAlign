"use client";

import { useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useToast } from "@/components/ui/toast";
import { ApiError } from "@/lib/api-client";
import { useUploadKnowledgeDocument } from "../hooks/use-knowledge-documents";
import { DOCUMENT_CATEGORY_LABELS, type DocumentCategory } from "../types";

const CATEGORIES = Object.keys(DOCUMENT_CATEGORY_LABELS) as DocumentCategory[];

export function DocumentUpload({ onUploaded }: { onUploaded?: () => void }) {
  const [title, setTitle] = useState("");
  const [category, setCategory] = useState<DocumentCategory>("policy");
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const upload = useUploadKnowledgeDocument();
  const toast = useToast();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!file || !title.trim()) return;
    setError(null);
    try {
      await upload.mutateAsync({ file, title: title.trim(), category });
      toast.success("Uploaded — Compass is processing it");
      setTitle("");
      setCategory("policy");
      setFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
      onUploaded?.();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Upload failed.");
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="flex flex-col gap-4 rounded-lg border border-line bg-white p-5 text-left"
    >
      <div className="grid gap-4 sm:grid-cols-[1fr_180px]">
        <Input
          label="Title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="e.g. Remote Work Policy"
          disabled={upload.isPending}
        />
        <div>
          <label htmlFor="knowledge-category" className="block text-sm font-medium text-ink">
            Category
          </label>
          <select
            id="knowledge-category"
            value={category}
            onChange={(e) => setCategory(e.target.value as DocumentCategory)}
            disabled={upload.isPending}
            className="mt-1.5 w-full rounded-md border border-line bg-white px-3 py-2.5 text-sm text-ink transition-colors focus:border-ink/30 focus:outline-none focus:ring-2 focus:ring-accent/30"
          >
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>
                {DOCUMENT_CATEGORY_LABELS[c]}
              </option>
            ))}
          </select>
        </div>
      </div>

      <label
        htmlFor="knowledge-file-input"
        className="flex cursor-pointer items-center justify-between gap-3 rounded-md border border-dashed border-line px-4 py-3 text-sm transition-colors focus-within:ring-2 focus-within:ring-accent/30 hover:border-ink/30"
      >
        <span className={`truncate ${file ? "text-ink" : "text-ink/50"}`}>
          {file ? file.name : "Choose a PDF, DOCX or TXT file"}
        </span>
        <span className="shrink-0 text-xs text-ink/40">Up to 20 MB</span>
        <input
          id="knowledge-file-input"
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,.txt"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          disabled={upload.isPending}
          className="sr-only"
        />
      </label>

      <div className="flex items-center gap-3">
        <Button type="submit" disabled={upload.isPending || !file || !title.trim()}>
          {upload.isPending ? "Uploading…" : "Upload"}
        </Button>
        {error && <p className="text-sm text-red-600">{error}</p>}
      </div>
    </form>
  );
}
