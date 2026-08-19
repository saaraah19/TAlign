import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { knowledgeApi } from "../api";
import { isDocumentProcessing, type DocumentCategory } from "../types";

const documentsKey = (params?: { category?: DocumentCategory; page?: number }) =>
  ["knowledge", "documents", params] as const;

export function useKnowledgeDocuments(params?: { category?: DocumentCategory; page?: number }) {
  return useQuery({
    queryKey: documentsKey(params),
    queryFn: () => knowledgeApi.list(params),
    // Keep polling while any document is still mid-pipeline (chunked,
    // waiting on the background embedding step) — same
    // "refetch until every row has settled" shape as
    // useAnalysisStatus/useMyAnalysisStatus in features/applications.
    refetchInterval: (query) => {
      const items = query.state.data?.items;
      if (!items) return false;
      return items.some((doc) => isDocumentProcessing(doc.status)) ? 3000 : false;
    },
  });
}

export function useUploadKnowledgeDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      file,
      title,
      category,
    }: {
      file: File;
      title: string;
      category: DocumentCategory;
    }) => knowledgeApi.upload(file, title, category),
    // onSettled, not onSuccess — the UI should always re-sync with real
    // server state regardless of whether the client believes this
    // request succeeded (see useTransitionJob's docstring in
    // features/jobs for the full reasoning; same lesson applies here).
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["knowledge", "documents"] });
    },
  });
}

export function useDeleteKnowledgeDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (documentId: string) => knowledgeApi.delete(documentId),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["knowledge", "documents"] });
    },
  });
}

export function useReindexKnowledgeDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (documentId: string) => knowledgeApi.reindex(documentId),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["knowledge", "documents"] });
    },
  });
}
