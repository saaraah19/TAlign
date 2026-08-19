export type DocumentCategory = "policy" | "benefits" | "procedure" | "other";

export type DocumentStatus =
  | "uploaded"
  | "text_extracted"
  | "chunked"
  | "embedded"
  | "ready"
  | "failed";

export interface KnowledgeDocument {
  id: string;
  title: string;
  category: DocumentCategory;
  original_filename: string;
  content_type: string;
  file_size_bytes: number;
  status: DocumentStatus;
  error_message: string | null;
  embedding_model: string | null;
  embedding_dimension: number | null;
  embedding_version: string | null;
  last_processed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface KnowledgeDocumentListResponse {
  items: KnowledgeDocument[];
  total: number;
  page: number;
  page_size: number;
}

export const DOCUMENT_CATEGORY_LABELS: Record<DocumentCategory, string> = {
  policy: "Policy",
  benefits: "Benefits",
  procedure: "Procedure",
  other: "Other",
};

export const DOCUMENT_STATUS_LABELS: Record<DocumentStatus, string> = {
  uploaded: "Uploaded",
  text_extracted: "Extracting text",
  chunked: "Chunking",
  embedded: "Embedding",
  ready: "Ready",
  failed: "Failed",
};

// Pipeline runs UPLOADED -> TEXT_EXTRACTED -> CHUNKED synchronously
// during upload, then CHUNKED -> EMBEDDED -> READY as a background
// task (see backend's KnowledgeDocumentService). By the time the
// frontend can see a document, it should already be at least CHUNKED
// — but a document can still be "in progress" toward READY/FAILED, so
// the list keeps polling until every document has settled.
const ACTIVE_DOCUMENT_STATES = new Set<DocumentStatus>([
  "uploaded",
  "text_extracted",
  "chunked",
  "embedded",
]);

export function isDocumentProcessing(status: DocumentStatus): boolean {
  return ACTIVE_DOCUMENT_STATES.has(status);
}
