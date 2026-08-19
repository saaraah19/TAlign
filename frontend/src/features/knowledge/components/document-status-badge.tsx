import { DOCUMENT_STATUS_LABELS, type DocumentStatus } from "../types";

const STATUS_STYLES: Record<DocumentStatus, string> = {
  uploaded: "bg-gray-100 text-gray-700",
  text_extracted: "bg-blue-100 text-blue-700",
  chunked: "bg-blue-100 text-blue-700",
  embedded: "bg-blue-100 text-blue-700",
  ready: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-700",
};

export function DocumentStatusBadge({ status }: { status: DocumentStatus }) {
  return (
    <span
      className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_STYLES[status]}`}
    >
      {DOCUMENT_STATUS_LABELS[status]}
    </span>
  );
}
