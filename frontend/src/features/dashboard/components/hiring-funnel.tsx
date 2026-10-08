import { Card } from "@/components/ui/card";

const STAGES: { key: string; label: string }[] = [
  { key: "applied", label: "Applied" },
  { key: "screening", label: "Screening" },
  { key: "interview", label: "Interview" },
  { key: "offer", label: "Offer" },
  { key: "hired", label: "Hired" },
];

export function HiringFunnel({ stageCounts }: { stageCounts: Record<string, number> }) {
  const max = Math.max(1, ...STAGES.map((s) => stageCounts[s.key] ?? 0));

  return (
    <Card className="p-6">
      <h2 className="text-sm font-medium text-ink">Hiring pipeline</h2>
      <div className="mt-5 grid grid-cols-5 gap-3">
        {STAGES.map((stage) => {
          const count = stageCounts[stage.key] ?? 0;
          const heightPct = Math.max(6, (count / max) * 100);
          return (
            <div key={stage.key} className="flex flex-col items-center">
              <div className="flex h-24 w-full items-end rounded-md bg-ink/[0.04]">
                <div
                  className="w-full rounded-md bg-ink/80"
                  style={{ height: `${heightPct}%` }}
                />
              </div>
              <p className="mt-2 text-lg font-semibold text-ink">{count}</p>
              <p className="text-xs text-ink/45">{stage.label}</p>
            </div>
          );
        })}
      </div>
    </Card>
  );
}
