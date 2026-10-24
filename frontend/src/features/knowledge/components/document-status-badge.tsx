import { Badge } from "@/components/ui/badge";
import { DOCUMENT_STATUS_LABELS, type DocumentStatus } from "../types";

const STATUS_TONES = {
  uploaded: "neutral",
  text_extracted: "info",
  chunked: "info",
  embedded: "info",
  ready: "success",
  failed: "danger",
} as const;

export function DocumentStatusBadge({ status }: { status: DocumentStatus }) {
  return <Badge tone={STATUS_TONES[status]}>{DOCUMENT_STATUS_LABELS[status]}</Badge>;
}
