export type ResumeStatus = "uploaded" | "parse_failed" | "text_ready";

export interface Resume {
  id: string;
  candidate_id: string;
  original_filename: string;
  content_type: string;
  file_size_bytes: number;
  status: ResumeStatus;
  parse_error: string | null;
  created_at: string;
}
