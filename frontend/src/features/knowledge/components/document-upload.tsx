"use client";

import { useRef, useState } from "react";
import { ApiError } from "@/lib/api-client";
import { useUploadKnowledgeDocument } from "../hooks/use-knowledge-documents";
import { DOCUMENT_CATEGORY_LABELS, type DocumentCategory } from "../types";

const CATEGORIES = Object.keys(DOCUMENT_CATEGORY_LABELS) as DocumentCategory[];

export function DocumentUpload() {
  const [title, setTitle] = useState("");
  const [category, setCategory] = useState<DocumentCategory>("policy");
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const upload = useUploadKnowledgeDocument();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!file || !title.trim()) return;
    setError(null);
    try {
      await upload.mutateAsync({ file, title: title.trim(), category });
      setTitle("");
      setCategory("policy");
      setFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Upload failed.");
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="flex flex-col gap-3 rounded-lg border border-gray-200 p-4"
    >
      <p className="text-sm font-medium text-gray-900">Upload a document</p>

      <div className="flex flex-col gap-1">
        <label htmlFor="knowledge-title" className="text-xs font-medium text-gray-500">
          Title
        </label>
        <input
          id="knowledge-title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="e.g. Remote Work Policy"
          disabled={upload.isPending}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm"
        />
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="knowledge-category" className="text-xs font-medium text-gray-500">
          Category
        </label>
        <select
          id="knowledge-category"
          value={category}
          onChange={(e) => setCategory(e.target.value as DocumentCategory)}
          disabled={upload.isPending}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm"
        >
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>
              {DOCUMENT_CATEGORY_LABELS[c]}
            </option>
          ))}
        </select>
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="knowledge-file-input" className="text-xs font-medium text-gray-500">
          File
        </label>
        <input
          id="knowledge-file-input"
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,.txt"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          disabled={upload.isPending}
          className="text-sm"
        />
        <p className="text-xs text-gray-400">PDF, DOCX, or TXT. Up to 20 MB.</p>
      </div>

      <button
        type="submit"
        disabled={upload.isPending || !file || !title.trim()}
        className="self-start rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
      >
        {upload.isPending ? "Uploading…" : "Upload"}
      </button>

      {error && <p className="text-sm text-red-600">{error}</p>}
    </form>
  );
}
