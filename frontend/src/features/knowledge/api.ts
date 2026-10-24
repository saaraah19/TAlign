import { apiFetch, apiFetchFormData } from "@/lib/api-client";
import type { DocumentCategory, KnowledgeDocument, KnowledgeDocumentListResponse } from "./types";

export const knowledgeApi = {
  upload: (file: File, title: string, category: DocumentCategory) => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("title", title);
    formData.append("category", category);
    return apiFetchFormData<KnowledgeDocument>("/knowledge/documents", formData);
  },

  list: (params?: { category?: DocumentCategory; page?: number; pageSize?: number }) => {
    const search = new URLSearchParams();
    if (params?.category) search.set("category", params.category);
    if (params?.page) search.set("page", String(params.page));
    if (params?.pageSize) search.set("page_size", String(params.pageSize));
    const query = search.toString();
    return apiFetch<KnowledgeDocumentListResponse>(
      `/knowledge/documents${query ? `?${query}` : ""}`,
    );
  },

  get: (documentId: string) => apiFetch<KnowledgeDocument>(`/knowledge/documents/${documentId}`),

  delete: (documentId: string) =>
    apiFetch<void>(`/knowledge/documents/${documentId}`, { method: "DELETE" }),

  reindex: (documentId: string) =>
    apiFetch<KnowledgeDocument>(`/knowledge/documents/${documentId}/reindex`, {
      method: "POST",
    }),
};
