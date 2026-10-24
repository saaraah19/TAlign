/**
 * Shared thresholds for reading an alignment score at a glance.
 * Mirrors the colour breakpoints already used on the Kanban cards
 * (80 / 60), so a candidate never looks "green" on the board and
 * "amber" on their own page.
 */
export type ScoreBand = "strong" | "moderate" | "limited";

export function scoreBand(score: number): ScoreBand {
  if (score >= 80) return "strong";
  if (score >= 60) return "moderate";
  return "limited";
}

export const SCORE_BAND_LABELS: Record<ScoreBand, string> = {
  strong: "Strong alignment",
  moderate: "Moderate alignment",
  limited: "Limited alignment",
};

export const SCORE_BAND_STROKE: Record<ScoreBand, string> = {
  strong: "stroke-emerald-500",
  moderate: "stroke-amber-500",
  limited: "stroke-ink/40",
};

export const SCORE_BAND_TEXT: Record<ScoreBand, string> = {
  strong: "text-emerald-600",
  moderate: "text-amber-600",
  limited: "text-ink/60",
};
