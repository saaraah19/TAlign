import { useQuery } from "@tanstack/react-query";
import { employeesApi } from "../api";

/**
 * Polls every 2s while no WorkflowRun has been recorded yet — the hire
 * workflow runs as a FastAPI BackgroundTask (see
 * app/workflow_engine/tasks.py), so there's a short window after the
 * transition-to-HIRED request returns where the workflow hasn't
 * finished yet. Same polling shape as useAnalysisStatus in
 * features/applications, applied to a different "is there a result
 * yet" signal (presence of workflow_run, rather than a status enum).
 */
export function useHireWorkflowStatus(applicationId: string, options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: ["applications", applicationId, "hire-workflow"],
    queryFn: () => employeesApi.getHireWorkflowStatus(applicationId),
    enabled: (options?.enabled ?? true) && Boolean(applicationId),
    refetchInterval: (query) => (query.state.data?.workflow_run ? false : 2000),
  });
}
