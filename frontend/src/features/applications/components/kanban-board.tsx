"use client";

import { useState } from "react";
import { useJobs } from "@/features/jobs";
import type { ApplicationStatus } from "../types";
import { KanbanColumn } from "./kanban-column";

const COLUMNS: { status: ApplicationStatus; label: string }[] = [
  { status: "applied", label: "Applied" },
  { status: "screening", label: "Screening" },
  { status: "interview", label: "Interview" },
  { status: "offer", label: "Offer" },
  { status: "hired", label: "Hired" },
];

/**
 * A real Kanban board, scoped to the state machine that actually
 * exists: ApplicationService._ALLOWED_TRANSITIONS is strictly forward
 * (applied → screening → interview → offer → hired) plus reject from
 * any non-terminal stage — there's no "move any card to any column"
 * rule to honor, so this isn't drag-and-drop between arbitrary
 * columns. Each card gets an "Advance →" button to its one legal next
 * stage instead, plus Reject where applicable — the same two actions
 * the backend actually allows, just visible per-card instead of
 * reachable only from a detail page.
 */
export function KanbanBoard({ initialJobId }: { initialJobId?: string }) {
  const [jobId, setJobId] = useState<string | undefined>(initialJobId);
  const [search, setSearch] = useState("");
  const { data: jobsData } = useJobs({ status: "open" });

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <select
          value={jobId ?? ""}
          onChange={(e) => setJobId(e.target.value || undefined)}
          className="rounded-md border border-line px-3 py-2 text-sm text-ink focus:border-ink/30 focus:outline-none sm:w-56"
        >
          <option value="">All open roles</option>
          {jobsData?.items.map((job) => (
            <option key={job.id} value={job.id}>
              {job.title}
            </option>
          ))}
        </select>
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search candidates…"
          className="w-full rounded-md border border-line px-3 py-2 text-sm placeholder:text-ink/30 focus:border-ink/30 focus:outline-none sm:w-64"
        />
      </div>

      <div className="flex gap-4 overflow-x-auto pb-2">
        {COLUMNS.map((col) => (
          <KanbanColumn
            key={col.status}
            status={col.status}
            label={col.label}
            jobId={jobId}
            search={search}
          />
        ))}
      </div>
    </div>
  );
}
