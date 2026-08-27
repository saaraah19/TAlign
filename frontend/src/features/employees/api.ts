import { apiFetch } from "@/lib/api-client";
import type { HireWorkflowStatus } from "./types";

export const employeesApi = {
  getHireWorkflowStatus: (applicationId: string) =>
    apiFetch<HireWorkflowStatus>(`/applications/${applicationId}/hire-workflow`),
};
