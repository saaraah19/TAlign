import Link from "next/link";
import type { RecentAnalysis } from "../types";
import { Section } from "./section";

export function RecentAnalysesSection({ analyses }: { analyses: RecentAnalysis[] }) {
  return (
    <Section title="Recent AI analyses" empty={analyses.length === 0}>
      <ul className="divide-y divide-gray-200 rounded-lg border border-gray-200">
        {analyses.map((analysis) => (
          <li key={analysis.analysis_id}>
            <Link
              href={`/pipeline/${analysis.application_id}`}
              className="flex flex-col gap-1 px-4 py-3 hover:bg-gray-50 sm:flex-row sm:items-center sm:justify-between sm:gap-0"
            >
              <div>
                <p className="text-sm font-medium text-gray-900">{analysis.candidate_name}</p>
                <p className="text-xs text-gray-500">{analysis.job_title}</p>
              </div>
              <span className="text-sm font-medium text-gray-900">
                {analysis.overall_score !== null ? `${analysis.overall_score.toFixed(1)}/100` : "—"}
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </Section>
  );
}
