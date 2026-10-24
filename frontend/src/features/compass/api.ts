import { apiFetch } from "@/lib/api-client";

export interface CompassCitation {
  document_id: string;
  document_title: string;
  chunk_id: string;
  excerpt: string;
}

export interface CompassAskResponse {
  message: string;
  capability_used: string | null;
  // Only populated for capability_used === "knowledge_query".
  citations: CompassCitation[] | null;
  confidence: "high" | "medium" | "low" | null;
}

export const compassApi = {
  // applicationId is optional — omit it to ask a general company
  // question (Knowledge Agent) rather than one scoped to a specific
  // candidate's analysis. See app/compass/compass.py's
  // _resolve_capability_for_role on the backend for how the presence
  // or absence of this field drives routing.
  ask: (message: string, applicationId?: string) =>
    apiFetch<CompassAskResponse>("/compass/ask", {
      method: "POST",
      body: JSON.stringify({
        message,
        ...(applicationId ? { application_id: applicationId } : {}),
      }),
    }),
};
