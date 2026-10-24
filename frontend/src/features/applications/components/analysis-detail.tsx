"use client";

import { useState } from "react";
import { AIMark } from "@/components/ui/ai-mark";
import { Button } from "@/components/ui/button";
import { useToast } from "@/components/ui/toast";
import { ApiError } from "@/lib/api-client";
import { useAnalysis, useAnalysisStatus, useReanalyze } from "../hooks/use-applications";
import { ANALYSIS_PROGRESS_LABELS } from "../types";
import { DimensionBars } from "./analysis/dimension-bars";
import { ExperienceFitCard } from "./analysis/experience-fit-card";
import { Insights } from "./analysis/insights";
import { ScoreGauge } from "./analysis/score-gauge";
import { SkillEvidenceList } from "./analysis/skill-evidence-list";

function SectionTitle() {
  return (
    <div className="flex items-center gap-2">
      <AIMark className="h-4 w-4 text-accent" />
      <h2 className="text-sm font-medium text-ink">Resume Intelligence</h2>
    </div>
  );
}

function StateCard({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-4">
      <SectionTitle />
      <div className="rounded-lg border border-line bg-white p-6">{children}</div>
    </div>
  );
}

/**
 * The recruiter's view of a resume analysis. This component owns the
 * *states* (loading / no resume / in progress / failed / complete);
 * each visual block of the complete state lives in ./analysis/ so no
 * single file grows past one idea. Everything shown comes straight
 * from the ResumeAnalysis the backend already returns — no figure
 * here is computed or invented on the client.
 */
export function AnalysisDetail({ applicationId }: { applicationId: string }) {
  const { data: statusData } = useAnalysisStatus(applicationId);
  const isComplete = statusData?.status === "complete";
  const { data: analysis, isLoading } = useAnalysis(applicationId, isComplete);
  const reanalyze = useReanalyze(applicationId);
  const toast = useToast();
  const [reanalyzeError, setReanalyzeError] = useState<string | null>(null);

  async function handleReanalyze() {
    setReanalyzeError(null);
    try {
      await reanalyze.mutateAsync();
      toast.info("Re-analysis started");
    } catch (err) {
      setReanalyzeError(err instanceof ApiError ? err.message : "Could not start re-analysis.");
    }
  }

  if (!statusData) {
    return (
      <StateCard>
        <div className="h-32 animate-pulse rounded-md bg-ink/[0.05]" />
      </StateCard>
    );
  }

  if (statusData.status === "not_started") {
    return (
      <StateCard>
        <p className="text-sm font-medium text-ink">No resume to analyze yet</p>
        <p className="mt-1 text-sm text-ink/55">
          The candidate hasn&apos;t attached a resume to this application. Once they do, Compass
          will read it and score the alignment with this role.
        </p>
      </StateCard>
    );
  }

  if (statusData.status === "parsing" || statusData.status === "analyzing") {
    return (
      <StateCard>
        <div className="flex items-center gap-3 text-sm text-ink/70">
          <span className="h-4 w-4 animate-spin rounded-full border-2 border-line border-t-ink" />
          {ANALYSIS_PROGRESS_LABELS[statusData.status]}
        </div>
      </StateCard>
    );
  }

  if (statusData.status === "failed") {
    return (
      <StateCard>
        <p className="text-sm font-medium text-red-600">Analysis failed</p>
        <p className="mt-1 text-sm text-ink/55">
          This can happen if the resume could not be read or the AI provider was unavailable.
        </p>
        {reanalyzeError && <p className="mt-2 text-sm text-red-600">{reanalyzeError}</p>}
        <Button
          variant="secondary"
          size="sm"
          className="mt-4"
          onClick={handleReanalyze}
          disabled={reanalyze.isPending}
        >
          {reanalyze.isPending ? "Retrying…" : "Try again"}
        </Button>
      </StateCard>
    );
  }

  if (isLoading || !analysis) {
    return (
      <StateCard>
        <div className="h-32 animate-pulse rounded-md bg-ink/[0.05]" />
      </StateCard>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <SectionTitle />

      <div className="rounded-lg border border-line bg-white p-6">
        <div className="flex flex-col gap-6 sm:flex-row sm:items-center sm:gap-10">
          <ScoreGauge score={analysis.overall_score} />
          <div className="flex-1">
            <DimensionBars
              required={analysis.required_skills_score_pct}
              preferred={analysis.preferred_skills_score_pct}
              experience={analysis.experience_score_pct}
            />
            <p className="mt-4 text-xs leading-relaxed text-ink/40">
              An analytical signal to help you evaluate this candidate — not a hiring decision.
            </p>
          </div>
        </div>
      </div>

      {analysis.explanation && (
        <div className="rounded-lg bg-ink p-5">
          <div className="flex items-center gap-2">
            <AIMark className="h-3.5 w-3.5 text-accent-light" />
            <p className="text-xs font-medium uppercase tracking-wide text-white/50">
              Compass assessment
            </p>
          </div>
          <p className="mt-2.5 text-sm leading-relaxed text-white/85">{analysis.explanation}</p>
        </div>
      )}

      <ExperienceFitCard fit={analysis.experience_fit} />

      <div className="flex flex-col gap-6 rounded-lg border border-line bg-white p-5">
        <SkillEvidenceList title="Required skills" matches={analysis.required_skills_result} />
        <SkillEvidenceList title="Preferred skills" matches={analysis.preferred_skills_result} />
      </div>

      <Insights strengths={analysis.strengths} concerns={analysis.potential_concerns} />

      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-xs text-ink/40">
          Analyzed {analysis.analyzed_at ? new Date(analysis.analyzed_at).toLocaleString() : "—"} ·
          Scoring v{analysis.scoring_algorithm_version} · {analysis.llm_provider}/
          {analysis.llm_model}
        </p>
        <div className="flex items-center gap-3">
          {reanalyzeError && <p className="text-xs text-red-600">{reanalyzeError}</p>}
          <Button
            variant="ghost"
            size="sm"
            onClick={handleReanalyze}
            disabled={reanalyze.isPending}
          >
            {reanalyze.isPending ? "Starting…" : "Re-analyze"}
          </Button>
        </div>
      </div>
    </div>
  );
}
