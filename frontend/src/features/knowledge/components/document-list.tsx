"use client";

import { useState } from "react";
import { ApiError } from "@/lib/api-client";
import {
  useDeleteKnowledgeDocument,
  useKnowledgeDocuments,
  useReindexKnowledgeDocument,
} from "../hooks/use-knowledge-documents";
import { DOCUMENT_CATEGORY_LABELS } from "../types";
import { DocumentStatusBadge } from "./document-status-badge";

export function DocumentList({ canManage }: { canManage: boolean }) {
  const { data, isLoading, error } = useKnowledgeDocuments();
  const deleteDocument = useDeleteKnowledgeDocument();
  const reindexDocument = useReindexKnowledgeDocument();
  const [actionError, setActionError] = useState<string | null>(null);
  const [pendingId, setPendingId] = useState<string | null>(null);

  if (isLoading) return <p className="text-sm text-gray-500">Loading documents…</p>;
  if (error) return <p className="text-sm text-red-600">Could not load documents.</p>;
  if (!data || data.items.length === 0) {
    return (
      <p className="text-sm text-gray-500">
        No documents yet — upload your first policy or handbook above.
      </p>
    );
  }

  async function handleDelete(documentId: string) {
    setActionError(null);
    setPendingId(documentId);
    try {
      await deleteDocument.mutateAsync(documentId);
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Could not delete that document.");
    } finally {
      setPendingId(null);
    }
  }

  async function handleReindex(documentId: string) {
    setActionError(null);
    setPendingId(documentId);
    try {
      await reindexDocument.mutateAsync(documentId);
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Could not reindex that document.");
    } finally {
      setPendingId(null);
    }
  }

  return (
    <div className="flex flex-col gap-3">
      <ul className="divide-y divide-gray-200 rounded-lg border border-gray-200">
        {data.items.map((doc) => {
          const isBusy = pendingId === doc.id;
          return (
            <li key={doc.id} className="flex items-center justify-between gap-3 px-4 py-3">
              <div className="min-w-0">
                <p className="truncate text-sm font-medium text-gray-900">{doc.title}</p>
                <p className="text-xs text-gray-500">
                  {DOCUMENT_CATEGORY_LABELS[doc.category]} · {doc.original_filename}
                </p>
                {doc.status === "failed" && doc.error_message && (
                  <p className="mt-1 text-xs text-red-600">{doc.error_message}</p>
                )}
              </div>

              <div className="flex shrink-0 items-center gap-2">
                <DocumentStatusBadge status={doc.status} />
                {canManage && (
                  <>
                    <button
                      onClick={() => handleReindex(doc.id)}
                      disabled={isBusy}
                      className="rounded-md border border-gray-300 px-2.5 py-1 text-xs font-medium text-gray-700 disabled:opacity-50"
                    >
                      Reindex
                    </button>
                    <button
                      onClick={() => handleDelete(doc.id)}
                      disabled={isBusy}
                      className="rounded-md border border-red-200 px-2.5 py-1 text-xs font-medium text-red-600 disabled:opacity-50"
                    >
                      Delete
                    </button>
                  </>
                )}
              </div>
            </li>
          );
        })}
      </ul>

      {actionError && <p className="text-sm text-red-600">{actionError}</p>}
    </div>
  );
}
