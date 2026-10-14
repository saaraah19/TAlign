"use client";

import { Skeleton } from "@/components/ui/skeleton";
import { usePipeline } from "../hooks/use-applications";
import type { ApplicationStatus } from "../types";
import { KanbanCard } from "./kanban-card";

// What an empty column is *for* — more useful than a bare "No candidates here".
const EMPTY_HINTS: Partial<Record<ApplicationStatus, string>> = {
  applied: "New applications land here",
  screening: "Move candidates here once you've reviewed them",
  interview: "Candidates you're interviewing",
  offer: "Candidates with an offer out",
  hired: "Hired candidates appear here",
};

export function KanbanColumn({
  status,
  label,
  jobId,
  search,
}: {
  status: ApplicationStatus;
  label: string;
  jobId?: string;
  search: string;
}) {
  const { data, isLoading } = usePipeline({ status, job_id: jobId });

  const items = (data?.items ?? []).filter((app) => {
    if (!search) return true;
    const name = `${app.candidate.first_name} ${app.candidate.last_name}`.toLowerCase();
    return name.includes(search.toLowerCase());
  });

  return (
    <div className="flex w-72 shrink-0 flex-col gap-3">
      <div className="flex items-center justify-between px-0.5">
        <p className="text-xs font-medium uppercase tracking-wide text-ink/45">{label}</p>
        <span className="text-xs font-medium text-ink/35">{data?.total ?? "—"}</span>
      </div>

      <div className="flex flex-col gap-2.5">
        {isLoading && (
          <>
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-24 w-full" />
          </>
        )}
        {!isLoading && items.length === 0 && (
          <div className="rounded-lg border border-dashed border-line px-3 py-8 text-center">
            <p className="text-xs text-ink/35">
              {search ? "No candidate matches" : (EMPTY_HINTS[status] ?? "No candidates here")}
            </p>
          </div>
        )}
        {items.map((app) => (
          <KanbanCard key={app.id} application={app} />
        ))}
      </div>
    </div>
  );
}
