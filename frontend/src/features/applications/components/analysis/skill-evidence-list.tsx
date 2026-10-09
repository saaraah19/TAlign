"use client";

import { useState } from "react";
import type { SkillMatch } from "../../types";

const COLLAPSED_COUNT = 6;

function StateIcon({ state }: { state: SkillMatch["match_state"] }) {
  if (state === "matched") {
    return (
      <span className="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-emerald-100 text-emerald-700">
        <svg viewBox="0 0 12 12" className="h-2.5 w-2.5" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M2.5 6.5l2.2 2.2L9.5 3.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </span>
    );
  }
  if (state === "not_matched") {
    return (
      <span className="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-red-100 text-red-600">
        <svg viewBox="0 0 12 12" className="h-2.5 w-2.5" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M3 3l6 6M9 3l-6 6" strokeLinecap="round" />
        </svg>
      </span>
    );
  }
  return (
    <span className="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-ink/[0.07] text-ink/40">
      <svg viewBox="0 0 12 12" className="h-2.5 w-2.5" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M3 6h6" strokeLinecap="round" />
      </svg>
    </span>
  );
}

const STATE_SR_LABEL: Record<SkillMatch["match_state"], string> = {
  matched: "Matched",
  not_matched: "Not matched",
  insufficient_evidence: "Insufficient evidence",
};

/**
 * One group of skills (required or preferred). Shows "4 of 6 matched"
 * up front so the recruiter gets the verdict before reading any row,
 * and collapses long lists — progressive disclosure, not a wall.
 */
export function SkillEvidenceList({
  title,
  matches,
}: {
  title: string;
  matches: SkillMatch[];
}) {
  const [expanded, setExpanded] = useState(false);
  if (matches.length === 0) return null;

  const matchedCount = matches.filter((m) => m.match_state === "matched").length;
  const visible = expanded ? matches : matches.slice(0, COLLAPSED_COUNT);
  const hiddenCount = matches.length - visible.length;

  return (
    <div>
      <div className="flex items-baseline justify-between">
        <p className="text-sm font-medium text-ink">{title}</p>
        <p className="text-xs text-ink/45">
          {matchedCount} of {matches.length} matched
        </p>
      </div>
      <ul className="mt-2 divide-y divide-line">
        {visible.map((m) => (
          <li key={m.skill} className="flex items-start gap-2.5 py-2.5">
            <StateIcon state={m.match_state} />
            <div className="min-w-0">
              <p className="text-sm text-ink">
                {m.skill}
                <span className="sr-only"> — {STATE_SR_LABEL[m.match_state]}</span>
              </p>
              {m.evidence && (
                <p className="mt-0.5 text-xs leading-relaxed text-ink/50">{m.evidence}</p>
              )}
            </div>
          </li>
        ))}
      </ul>
      {matches.length > COLLAPSED_COUNT && (
        <button
          onClick={() => setExpanded((v) => !v)}
          className="mt-1 text-xs font-medium text-ink/50 hover:text-ink"
        >
          {expanded ? "Show fewer" : `Show ${hiddenCount} more`}
        </button>
      )}
    </div>
  );
}
