export type EmailType = "rejection" | "interview_invitation";
export type EmailStatus = "draft" | "sent";

export const EMAIL_TYPE_LABELS: Record<EmailType, string> = {
  rejection: "Rejection",
  interview_invitation: "Interview invitation",
};

export interface Email {
  id: string;
  application_id: string;
  email_type: EmailType;
  status: EmailStatus;
  recipient_email: string;
  subject: string;
  body: string;
  llm_provider: string | null;
  llm_model: string | null;
  prompt_version: string | null;
  sent_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface EmailListResponse {
  items: Email[];
}
