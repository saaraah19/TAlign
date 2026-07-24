import { apiFetch } from "@/lib/api-client";

export interface CompassAskResponse {
  message: string;
  capability_used: string | null;
}

export const compassApi = {
  ask: (applicationId: string, message: string) =>
    apiFetch<CompassAskResponse>("/compass/ask", {
      method: "POST",
      body: JSON.stringify({ application_id: applicationId, message }),
    }),
};
