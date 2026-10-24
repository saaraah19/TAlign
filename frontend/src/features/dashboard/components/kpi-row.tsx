import { Card } from "@/components/ui/card";
import type { DashboardKPIs } from "../types";

export function KpiRow({ kpis }: { kpis: DashboardKPIs }) {
  const items = [
    { label: "Open roles", value: kpis.open_jobs },
    { label: "Active candidates", value: kpis.active_candidates },
    { label: "Interviewing", value: kpis.interviewing },
    { label: "Pending actions", value: kpis.pending_actions },
  ];

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
      {items.map((item) => (
        <Card key={item.label} className="p-5">
          <p className="text-2xl font-semibold tracking-tight text-ink">{item.value}</p>
          <p className="mt-1 text-xs font-medium text-ink/45">{item.label}</p>
        </Card>
      ))}
    </div>
  );
}
