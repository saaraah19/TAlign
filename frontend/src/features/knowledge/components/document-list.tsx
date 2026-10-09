"use client";

import { useState } from "react";
import { DOCUMENT_CATEGORY_LABELS, type DocumentCategory, type KnowledgeDocument } from "../types";
import { DocumentRow } from "./document-row";

const CATEGORY_ORDER: DocumentCategory[] = ["policy", "benefits", "procedure", "other"];

/**
 * The document library, grouped by category. Purely presentational:
 * it receives the documents already fetched by KnowledgeCenter and
 * only decides how to arrange them. Category counts are counted from
 * those same documents, so they can never disagree with what's listed.
 */
export function DocumentList({
  documents,
  canManage,
}: {
  documents: KnowledgeDocument[];
  canManage: boolean;
}) {
  const [filter, setFilter] = useState<DocumentCategory | "all">("all");

  const byCategory = CATEGORY_ORDER.map((category) => ({
    category,
    docs: documents.filter((d) => d.category === category),
  })).filter((group) => group.docs.length > 0);

  // If the selected category empties out (its last document deleted),
  // fall back to "all" instead of showing a blank library.
  const activeFilter =
    filter !== "all" && byCategory.some((g) => g.category === filter) ? filter : "all";
  const visibleGroups =
    activeFilter === "all" ? byCategory : byCategory.filter((g) => g.category === activeFilter);

  return (
    <div className="flex flex-col gap-6">
      {byCategory.length > 1 && (
        <div className="flex flex-wrap gap-2">
          <FilterChip
            label="All"
            count={documents.length}
            active={activeFilter === "all"}
            onClick={() => setFilter("all")}
          />
          {byCategory.map((g) => (
            <FilterChip
              key={g.category}
              label={DOCUMENT_CATEGORY_LABELS[g.category]}
              count={g.docs.length}
              active={activeFilter === g.category}
              onClick={() => setFilter(g.category)}
            />
          ))}
        </div>
      )}

      {visibleGroups.map((group) => (
        <section key={group.category}>
          <div className="mb-2 flex items-baseline gap-2">
            <h3 className="text-sm font-medium text-ink">
              {DOCUMENT_CATEGORY_LABELS[group.category]}
            </h3>
            <span className="text-xs text-ink/40">{group.docs.length}</span>
          </div>
          <ul className="divide-y divide-line rounded-lg border border-line bg-white">
            {group.docs.map((doc) => (
              <DocumentRow key={doc.id} document={doc} canManage={canManage} />
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}

function FilterChip({
  label,
  count,
  active,
  onClick,
}: {
  label: string;
  count: number;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
        active ? "bg-ink text-white" : "bg-ink/[0.05] text-ink/65 hover:bg-ink/[0.09]"
      }`}
    >
      {label} <span className={active ? "text-white/60" : "text-ink/35"}>{count}</span>
    </button>
  );
}
