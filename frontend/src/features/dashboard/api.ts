import { apiFetch } from "@/lib/api-client";
import type { DashboardData } from "./types";

export const dashboardApi = {
  get: () => apiFetch<DashboardData>("/dashboard"),
};
