"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { useToast } from "@/components/ui/toast";
import { ApiError } from "@/lib/api-client";
import { formatFileSize } from "@/lib/format-file-size";
import { formatRelativeTime } from "@/lib/format-relative-time";
import {
  useDeleteKnowledgeDocument,
  useReindexKnowledgeDocument,
} from "../hooks/use-knowledge-documents";
import type { KnowledgeDocument } from "../types";
import { DocumentStatusBadge } from "./document-status-badge";

function fileExtension(filename: string): string {
  const dot = filename.lastIndexOf(".");
  return dot === -1 ? "FILE" : filename.slice(dot + 1, dot + 5).toUpperCase();
}

/**
 * One document in the library. Delete is irreversible (it removes the
 * document and everything Compass learned from it), so it takes two
 * clicks — the same inline-confirm pattern as rejecting a candidate.
 */
export function DocumentRow({
  document: doc,
  canManage,
}: {
  document: KnowledgeDocument;
  canManage: boolean;
}) {
  const deleteDocument = useDeleteKnowledgeDocument();
  const reindexDocument = useReindexKnowledgeDocument();
  const toast = useToast();
  const [confirmingDelete, setConfirmingDelete] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const busy = deleteDocument.isPending || reindexDocument.isPending;

  async function handleDelete() {
    setError(null);
    try {
      await deleteDocument.mutateAsync(doc.id);
      toast.success("Document deleted");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not delete that document.");
      setConfirmingDelete(false);
    }
  }

  async function handleReindex() {
    setError(null);
    try {
      await reindexDocument.mutateAsync(doc.id);
      toast.success("Reindexing started");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not reindex that document.");
    }
  }

  return (
    <li className="px-4 py-3.5">
      <div className="flex items-center gap-4">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-ink/[0.05] text-[10px] font-semibold tracking-wide text-ink/55">
          {fileExtension(doc.original_filename)}
        </span>

        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium text-ink">{doc.title}</p>
          <p className="truncate text-xs text-ink/45">
            {doc.original_filename} · {formatFileSize(doc.file_size_bytes)} · Updated{" "}
            {formatRelativeTime(doc.updated_at)}
          </p>
        </div>

        <div className="flex shrink-0 items-center gap-2">
          <DocumentStatusBadge status={doc.status} />
          {canManage &&
            (confirmingDelete ? (
              <>
                <Button variant="danger" size="sm" onClick={handleDelete} disabled={busy}>
                  {deleteDocument.isPending ? "Deleting…" : "Confirm delete"}
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setConfirmingDelete(false)}
                  disabled={busy}
                >
                  Cancel
                </Button>
              </>
            ) : (
              <>
                <Button variant="ghost" size="sm" onClick={handleReindex} disabled={busy}>
                  {reindexDocument.isPending ? "Reindexing…" : "Reindex"}
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setConfirmingDelete(true)}
                  disabled={busy}
                  className="hover:!text-red-600"
                >
                  Delete
                </Button>
              </>
            ))}
        </div>
      </div>

      {doc.status === "failed" && doc.error_message && (
        <p className="mt-2 pl-14 text-xs text-red-600">{doc.error_message}</p>
      )}
      {error && <p className="mt-2 pl-14 text-xs text-red-600">{error}</p>}
    </li>
  );
}
