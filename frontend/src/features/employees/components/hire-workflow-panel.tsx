"use client";

import { useHireWorkflowStatus } from "../hooks/use-hire-workflow";
import { HIRE_WORKFLOW_STEP_LABELS, HIRE_WORKFLOW_STEP_ORDER } from "../types";
import { WorkflowRunStatusBadge } from "./workflow-run-status-badge";

/**
 * Only rendered once an Application has actually reached HIRED (the
 * parent page controls `enabled`) — the hire workflow doesn't exist
 * before that, so there's nothing to show. Mirrors the four steps in
 * app/workflow_engine/workflows/hire_candidate.py as a checklist, so
 * the workflow's real, live outcome is visible and not just its tests.
 */
export function HireWorkflowPanel({
  applicationId,
  enabled,
}: {
  applicationId: string;
  enabled: boolean;
}) {
  const { data, isLoading } = useHireWorkflowStatus(applicationId, { enabled });

  if (!enabled) return null;

  return (
    <div className="rounded-lg border border-line bg-white p-5">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-ink">Hire workflow</p>
        {data?.workflow_run && <WorkflowRunStatusBadge status={data.workflow_run.status} />}
      </div>

      {(isLoading || !data?.workflow_run) && (
        <div className="mt-3 flex items-center gap-2.5 text-sm text-ink/55">
          <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-line border-t-ink" />
          Running hire workflow…
        </div>
      )}

      {data?.workflow_run && (
        <>
          <ul className="mt-4 flex flex-col gap-2.5">
            {HIRE_WORKFLOW_STEP_ORDER.map((step) => (
              <StepRow
                key={step}
                label={HIRE_WORKFLOW_STEP_LABELS[step] ?? step}
                done={data.workflow_run!.completed_steps.includes(step)}
                failed={data.workflow_run!.failed_step === step}
              />
            ))}
          </ul>

          {data.workflow_run.status === "failed" && data.workflow_run.error && (
            <p className="mt-3 text-sm text-red-600">{data.workflow_run.error}</p>
          )}

          {data.workflow_run.status === "skipped" && (
            <p className="mt-3 text-xs text-ink/50">
              This workflow already ran for this application — nothing new was created.
            </p>
          )}
        </>
      )}

      {data?.employee && (
        <div className="mt-4 border-t border-line pt-4">
          <p className="text-sm font-medium text-ink">
            {data.employee.first_name} {data.employee.last_name}
          </p>
          <p className="text-xs text-ink/50">
            {data.employee.job_title} · Hired{" "}
            {new Date(data.employee.hire_date).toLocaleDateString()}
          </p>

          {data.onboarding_tasks.length > 0 && (
            <ul className="mt-3 flex flex-col gap-2">
              {data.onboarding_tasks.map((task) => (
                <li key={task.id} className="flex items-center gap-2.5 text-sm text-ink/75">
                  <span
                    className={`h-3.5 w-3.5 shrink-0 rounded-full border ${
                      task.completed ? "border-emerald-600 bg-emerald-600" : "border-line bg-white"
                    }`}
                  />
                  {task.title}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}

function StepRow({ label, done, failed }: { label: string; done: boolean; failed: boolean }) {
  return (
    <li className="flex items-center gap-2.5 text-sm">
      <span
        className={`flex h-4 w-4 shrink-0 items-center justify-center rounded-full border text-white ${
          failed
            ? "border-red-600 bg-red-600"
            : done
              ? "border-emerald-600 bg-emerald-600"
              : "border-line bg-white"
        }`}
      >
        {done && (
          <svg viewBox="0 0 12 12" className="h-2.5 w-2.5" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M2.5 6.5l2.2 2.2L9.5 3.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        )}
      </span>
      <span className={failed ? "text-red-600" : done ? "text-ink" : "text-ink/35"}>
        {label}
        {failed && " — failed"}
      </span>
    </li>
  );
}
