"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { policySuggestions } from "@/features/compass";
import { useKnowledgeDocuments } from "../hooks/use-knowledge-documents";
import { isDocumentProcessing } from "../types";
import { CompassHero } from "./compass-hero";
import { DocumentList } from "./document-list";
import { DocumentUpload } from "./document-upload";

// The backend caps one page at 100. Grouping by category needs every
// document in hand, so we ask for the maximum and say so honestly if
// a company ever has more (see the "Showing the first…" note below).
const PAGE_SIZE = 100;

/**
 * The whole Knowledge Center: header, Compass, library, and the four
 * situations a library can be in — loading, empty, documents but none
 * ready yet, and normal. Fetches once and hands the documents down.
 */
export function KnowledgeCenter({ canManage }: { canManage: boolean }) {
  const { data, isLoading, error } = useKnowledgeDocuments({ pageSize: PAGE_SIZE });
  const [showUpload, setShowUpload] = useState(false);

  if (isLoading) {
    return (
      <div className="flex flex-col gap-6">
        <div className="h-48 animate-pulse rounded-xl bg-ink/[0.05]" />
        <div className="h-40 animate-pulse rounded-lg bg-ink/[0.05]" />
      </div>
    );
  }
  if (error || !data) {
    return <p className="text-sm text-red-600">Could not load the Knowledge Center.</p>;
  }

  const documents = data.items;

  if (documents.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-line bg-white px-6 py-12 text-center">
        <h2 className="text-base font-semibold text-ink">
          Teach Compass your company&apos;s policies
        </h2>
        <p className="mx-auto mt-1.5 max-w-md text-sm leading-relaxed text-ink/55">
          Upload your handbook, leave policy or benefits guide. Once a document is processed,
          anyone here can ask Compass about it and get an answer with the source cited.
        </p>
        <div className="mx-auto mt-6 max-w-xl">
          {canManage ? (
            <DocumentUpload />
          ) : (
            <p className="text-sm text-ink/45">
              No documents have been uploaded yet. An admin can add them here.
            </p>
          )}
        </div>
      </div>
    );
  }

  const readyDocs = documents.filter((d) => d.status === "ready");
  const processingCount = documents.filter((d) => isDocumentProcessing(d.status)).length;
  const suggestions = policySuggestions(readyDocs.map((d) => d.title));

  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-sm text-ink/55">
          {data.total} {data.total === 1 ? "document" : "documents"} · {readyDocs.length} ready
          for Compass
          {processingCount > 0 && ` · ${processingCount} processing`}
        </p>
        {canManage && (
          <Button
            variant={showUpload ? "secondary" : "primary"}
            size="sm"
            onClick={() => setShowUpload((v) => !v)}
          >
            {showUpload ? "Close" : "Upload document"}
          </Button>
        )}
      </div>

      {canManage && showUpload && <DocumentUpload onUploaded={() => setShowUpload(false)} />}

      {readyDocs.length > 0 ? (
        <CompassHero suggestions={suggestions} />
      ) : (
        <div className="rounded-xl border border-line bg-white p-6">
          <p className="text-sm font-medium text-ink">Compass isn&apos;t ready yet</p>
          <p className="mt-1 text-sm text-ink/55">
            {processingCount > 0
              ? "Your documents are still being processed. Compass will be available as soon as the first one is ready."
              : "None of the documents could be processed, so Compass has nothing to answer from. See the errors below."}
          </p>
        </div>
      )}

      <DocumentList documents={documents} canManage={canManage} />

      {data.total > documents.length && (
        <p className="text-xs text-ink/40">
          Showing the first {documents.length} of {data.total} documents.
        </p>
      )}
    </div>
  );
}
