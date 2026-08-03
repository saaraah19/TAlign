import { apiFetch } from "@/lib/api-client";
import type { Email, EmailListResponse, EmailType } from "./types";

export const communicationApi = {
  draft: (applicationId: string, emailType: EmailType) =>
    apiFetch<Email>(`/applications/${applicationId}/emails/draft`, {
      method: "POST",
      body: JSON.stringify({ email_type: emailType }),
    }),

  regenerate: (applicationId: string, emailId: string) =>
    apiFetch<Email>(`/applications/${applicationId}/emails/${emailId}/regenerate`, {
      method: "POST",
    }),

  update: (applicationId: string, emailId: string, subject: string, body: string) =>
    apiFetch<Email>(`/applications/${applicationId}/emails/${emailId}`, {
      method: "PATCH",
      body: JSON.stringify({ subject, body }),
    }),

  send: (applicationId: string, emailId: string) =>
    apiFetch<Email>(`/applications/${applicationId}/emails/${emailId}/send`, {
      method: "POST",
    }),

  list: (applicationId: string) =>
    apiFetch<EmailListResponse>(`/applications/${applicationId}/emails`),
};
