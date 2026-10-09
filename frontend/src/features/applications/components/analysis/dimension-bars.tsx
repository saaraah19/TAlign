function DimensionBar({ label, pct }: { label: string; pct: number | null }) {
  return (
    <div>
      <div className="flex items-baseline justify-between text-xs">
        <span className="text-ink/60">{label}</span>
        <span className={pct === null ? "text-ink/35" : "font-medium text-ink"}>
          {pct === null ? "N/A" : `${Math.round(pct)}%`}
        </span>
      </div>
      <div className="mt-1.5 h-1.5 w-full rounded-full bg-ink/[0.07]">
        <div
          className="h-1.5 rounded-full bg-ink transition-[width] duration-700 ease-out"
          style={{ width: `${pct ?? 0}%` }}
        />
      </div>
    </div>
  );
}

/** The three sub-scores the overall score is built from. */
export function DimensionBars({
  required,
  preferred,
  experience,
}: {
  required: number | null;
  preferred: number | null;
  experience: number | null;
}) {
  return (
    <div className="flex flex-col gap-3.5">
      <DimensionBar label="Required skills" pct={required} />
      <DimensionBar label="Preferred skills" pct={preferred} />
      <DimensionBar label="Experience" pct={experience} />
    </div>
  );
}
