import { Badge } from "@/components/ui/badge";
import type { ExperienceFit } from "../../types";

/**
 * Experience fit was already returned by the backend (it feeds the
 * experience sub-score) but never shown — a recruiter saw "Experience
 * 62%" with no way to know why. This surfaces the reasoning.
 */
export function ExperienceFitCard({ fit }: { fit: ExperienceFit | null }) {
  if (!fit) return null;

  const years = fit.candidate_relevant_years;
  const verdict =
    fit.meets_minimum === true ? (
      <Badge tone="success">Meets minimum</Badge>
    ) : fit.meets_minimum === false ? (
      <Badge tone="warning">Below minimum</Badge>
    ) : (
      <Badge>Minimum unknown</Badge>
    );

  return (
    <div className="rounded-lg border border-line bg-white p-5">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm font-medium text-ink">Experience fit</p>
        {verdict}
      </div>
      <p className="mt-2 text-sm text-ink/70">
        {years === null
          ? "Relevant experience could not be determined from the resume."
          : `${years} ${years === 1 ? "year" : "years"} of relevant experience`}
      </p>
      {fit.justification && (
        <p className="mt-1.5 text-xs leading-relaxed text-ink/50">{fit.justification}</p>
      )}
    </div>
  );
}
