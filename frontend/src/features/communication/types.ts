// "onboarding_welcome" is never drafted from this panel's own buttons —
// it's created automatically by the Slice 7 hire workflow when an
// Application transitions to HIRED (see features/employees). It's
// listed here purely so EMAIL_TYPE_LABELS/EmailDraftCard render it
// correctly once it shows up in useEmails' list — regenerate/edit/send
// all still work on it exactly like the other two types, since the
// recruiter reviewing a system-drafted email before sending is the same
// "AI assists, humans decide" property either way.
export type EmailType = "rejection" | "interview_invitation" | "onboarding_welcome";
export type EmailStatus = "draft" | "sent";

export const EMAIL_TYPE_LABELS: Record<EmailType, string> = {
  rejection: "Rejection",
  interview_invitation: "Interview invitation",
  onboarding_welcome: "Welcome email",
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
