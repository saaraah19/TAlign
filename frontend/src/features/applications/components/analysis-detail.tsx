"use client";

import { useState } from "react";
import { ApiError } from "@/lib/api-client";
import { useAnalysis, useAnalysisStatus, useReanalyze } from "../hooks/use-applications";
import { ANALYSIS_PROGRESS_LABELS, type SkillMatch } from "../types";

const MATCH_STYLES: Record<SkillMatch["match_state"], string> = {
  matched: "bg-green-100 text-green-700",
  not_matched: "bg-red-100 text-red-700",
  insufficient_evidence: "bg-gray-100 text-gray-600",
};

const MATCH_LABELS: Record<SkillMatch["match_state"], string> = {
  matched: "Matched",
  not_matched: "Not matched",
  insufficient_evidence: "Insufficient evidence",
};

function SkillRow({ match }: { match: SkillMatch }) {
  return (
    <li className="flex items-start justify-between gap-3 py-1.5 text-sm">
      <div>
        <span className="font-medium text-gray-900">{match.skill}</span>
        {match.evidence && <p className="text-xs text-gray-500">{match.evidence}</p>}
      </div>
      <span
        className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${MATCH_STYLES[match.match_state]}`}
      >
        {MATCH_LABELS[match.match_state]}
      </span>
    </li>
  );
}

function DimensionBar({ label, pct }: { label: string; pct: number | null }) {
  return (
    <div>
      <div className="flex justify-between text-xs text-gray-500">
        <span>{label}</span>
        <span>{pct === null ? "N/A" : `${Math.round(pct)}%`}</span>
      </div>
      <div className="mt-1 h-1.5 w-full rounded-full bg-gray-100">
        <div className="h-1.5 rounded-full bg-gray-900" style={{ width: `${pct ?? 0}%` }} />
      </div>
    </div>
  );
}

export function AnalysisDetail({ applicationId }: { applicationId: string }) {
  const { data: statusData } = useAnalysisStatus(applicationId);
  const isComplete = statusData?.status === "complete";
  const { data: analysis, isLoading } = useAnalysis(applicationId, isComplete);
  const reanalyze = useReanalyze(applicationId);
  const [reanalyzeError, setReanalyzeError] = useState<string | null>(null);

  async function handleReanalyze() {
    setReanalyzeError(null);
    try {
      await reanalyze.mutateAsync();
    } catch (err) {
      setReanalyzeError(err instanceof ApiError ? err.message : "Could not start re-analysis.");
    }
  }

  if (!statusData) return <p className="text-sm text-gray-500">Loading…</p>;

  if (statusData.status === "not_started") {
    return <p className="text-sm text-gray-500">No resume has been attached yet.</p>;
  }
  if (statusData.status === "parsing" || statusData.status === "analyzing") {
    return (
      <div className="flex items-center gap-2 text-sm text-gray-600">
        <span className="h-3 w-3 animate-spin rounded-full border-2 border-gray-300 border-t-gray-900" />
        {ANALYSIS_PROGRESS_LABELS[statusData.status]}
      </div>
    );
  }
  if (statusData.status === "failed") {
    return (
      <div className="flex flex-col gap-2">
        <p className="text-sm text-red-600">
          Analysis failed. This can happen if the resume could not be read or the AI provider
          was unavailable.
        </p>
        <button
          onClick={handleReanalyze}
          disabled={reanalyze.isPending}
          className="w-fit rounded-md border border-gray-300 px-3 py-1.5 text-xs font-medium disabled:opacity-50"
        >
          {reanalyze.isPending ? "Retrying…" : "Try again"}
        </button>
      </div>
    );
  }

  if (isLoading || !analysis) return <p className="text-sm text-gray-500">Loading analysis…</p>;

  return (
    <div className="flex flex-col gap-5">
      <div>
        <div className="flex items-baseline justify-between">
          <p className="text-sm text-gray-500">
            Alignment score — an analytical signal to help you evaluate this candidate, not a
            hiring decision.
          </p>
          <p className="text-2xl font-semibold text-gray-900">
            {analysis.overall_score ?? "—"}
            <span className="text-sm font-normal text-gray-400">/100</span>
          </p>
        </div>

        <div className="mt-3 flex flex-col gap-2">
          <DimensionBar label="Required skills" pct={analysis.required_skills_score_pct} />
          <DimensionBar label="Preferred skills" pct={analysis.preferred_skills_score_pct} />
          <DimensionBar label="Experience" pct={analysis.experience_score_pct} />
        </div>
      </div>

      {analysis.explanation && (
        <p className="rounded-md bg-gray-50 p-3 text-sm text-gray-700">{analysis.explanation}</p>
      )}

      <div>
        <p className="text-sm font-medium text-gray-900">Required skills</p>
        <ul className="mt-1 divide-y divide-gray-100">
          {analysis.required_skills_result.map((m) => (
            <SkillRow key={m.skill} match={m} />
          ))}
        </ul>
      </div>

      {analysis.preferred_skills_result.length > 0 && (
        <div>
          <p className="text-sm font-medium text-gray-900">Preferred skills</p>
          <ul className="mt-1 divide-y divide-gray-100">
            {analysis.preferred_skills_result.map((m) => (
              <SkillRow key={m.skill} match={m} />
            ))}
          </ul>
        </div>
      )}

      {analysis.strengths.length > 0 && (
        <div>
          <p className="text-sm font-medium text-gray-900">Strengths</p>
          <ul className="mt-1 list-inside list-disc text-sm text-gray-700">
            {analysis.strengths.map((s) => (
              <li key={s}>{s}</li>
            ))}
          </ul>
        </div>
      )}

      {analysis.potential_concerns.length > 0 && (
        <div>
          <p className="text-sm font-medium text-gray-900">Potential concerns</p>
          <ul className="mt-1 list-inside list-disc text-sm text-gray-700">
            {analysis.potential_concerns.map((c) => (
              <li key={c}>{c}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="border-t border-gray-100 pt-3">
        {reanalyzeError && <p className="mb-2 text-sm text-red-600">{reanalyzeError}</p>}
        <button
          onClick={handleReanalyze}
          disabled={reanalyze.isPending}
          className="rounded-md border border-gray-300 px-3 py-1.5 text-xs font-medium disabled:opacity-50"
        >
          {reanalyze.isPending ? "Starting…" : "Re-analyze"}
        </button>
        <p className="mt-2 text-xs text-gray-400">
          Analyzed{" "}
          {analysis.analyzed_at ? new Date(analysis.analyzed_at).toLocaleString() : "—"} · Scoring
          v{analysis.scoring_algorithm_version} · {analysis.llm_provider}/{analysis.llm_model}
        </p>
      </div>
    </div>
  );
}
