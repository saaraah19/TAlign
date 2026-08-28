import { useQuery } from "@tanstack/react-query";
import { dashboardApi } from "../api";

export function useDashboard(options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: ["dashboard"],
    queryFn: dashboardApi.get,
    enabled: options?.enabled ?? true,
  });
}
