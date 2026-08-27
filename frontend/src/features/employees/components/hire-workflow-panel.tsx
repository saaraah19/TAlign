"use client";

import { useHireWorkflowStatus } from "../hooks/use-hire-workflow";
import { HIRE_WORKFLOW_STEP_LABELS, HIRE_WORKFLOW_STEP_ORDER } from "../types";
import { WorkflowRunStatusBadge } from "./workflow-run-status-badge";

/**
 * Only rendered once an Application has actually reached HIRED (the
 * parent page controls `enabled`) — the hire workflow doesn't exist
 * before that, so there's nothing to show. See
 * app/workflow_engine/workflows/hire_candidate.py for the three steps
 * this mirrors, and PROJECT_STATUS.md's "tests pass ≠ actually works"
 * lesson for why this exists at all: this panel is what makes the
 * hire workflow's real, live outcome visible, not just its test suite.
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
    <div className="flex flex-col gap-4">
      <h2 className="text-sm font-medium text-gray-900">Hire workflow</h2>

      {isLoading && <p className="text-sm text-gray-500">Checking hire workflow…</p>}

      {!isLoading && !data?.workflow_run && (
        <p className="text-sm text-gray-500">Running hire workflow…</p>
      )}

      {data?.workflow_run && (
        <div className="rounded-lg border border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium uppercase tracking-wide text-gray-500">
              {data.workflow_run.workflow_name}
            </span>
            <WorkflowRunStatusBadge status={data.workflow_run.status} />
          </div>

          <ul className="mt-3 flex flex-col gap-1.5">
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
            <p className="mt-3 text-xs text-gray-500">
              This workflow already ran for this application — nothing new was created.
            </p>
          )}
        </div>
      )}

      {data?.employee && (
        <div className="rounded-lg border border-gray-200 p-4">
          <p className="text-sm font-medium text-gray-900">
            {data.employee.first_name} {data.employee.last_name}
          </p>
          <p className="text-xs text-gray-500">
            {data.employee.job_title} · Hired {new Date(data.employee.hire_date).toLocaleDateString()}
          </p>

          {data.onboarding_tasks.length > 0 && (
            <ul className="mt-3 flex flex-col gap-1.5">
              {data.onboarding_tasks.map((task) => (
                <li key={task.id} className="flex items-center gap-2 text-sm text-gray-700">
                  <span
                    className={`inline-block h-3.5 w-3.5 rounded-full border ${
                      task.completed
                        ? "border-green-600 bg-green-600"
                        : "border-gray-300 bg-white"
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
  const style = failed
    ? "border-red-600 bg-red-600"
    : done
      ? "border-green-600 bg-green-600"
      : "border-gray-300 bg-white";

  return (
    <li className="flex items-center gap-2 text-sm">
      <span className={`inline-block h-3.5 w-3.5 flex-shrink-0 rounded-full border ${style}`} />
      <span className={failed ? "text-red-600" : done ? "text-gray-900" : "text-gray-400"}>
        {label}
        {failed && " — failed"}
      </span>
    </li>
  );
}
