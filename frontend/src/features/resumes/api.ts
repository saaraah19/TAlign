import { apiFetch, apiFetchFormData } from "@/lib/api-client";
import type { Resume } from "./types";

export const resumesApi = {
  upload: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return apiFetchFormData<Resume>("/resumes", formData);
  },

  listMine: () => apiFetch<Resume[]>("/resumes/mine"),

  getMine: (resumeId: string) => apiFetch<Resume>(`/resumes/mine/${resumeId}`),
};
