import { WorkflowRunStatusBadge, type WorkflowRun } from "@/features/employees";
import { Section } from "./section";

export function RecentWorkflowRunsSection({ runs }: { runs: WorkflowRun[] }) {
  return (
    <Section title="Recent AI activity" empty={runs.length === 0}>
      <ul className="divide-y divide-gray-200 rounded-lg border border-gray-200">
        {runs.map((run) => (
          <li
            key={run.id}
            className="flex flex-col gap-1 px-4 py-3 sm:flex-row sm:items-center sm:justify-between sm:gap-0"
          >
            <div>
              <p className="text-sm font-medium text-gray-900">{run.workflow_name}</p>
              <p className="text-xs text-gray-500">
                {new Date(run.created_at).toLocaleString()}
              </p>
            </div>
            <WorkflowRunStatusBadge status={run.status} />
          </li>
        ))}
      </ul>
    </Section>
  );
}
