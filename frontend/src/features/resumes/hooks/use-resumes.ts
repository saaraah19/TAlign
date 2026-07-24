import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { resumesApi } from "../api";

export function useMyResumes() {
  return useQuery({
    queryKey: ["resumes", "mine"],
    queryFn: () => resumesApi.listMine(),
  });
}

export function useUploadResume() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => resumesApi.upload(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["resumes", "mine"] });
    },
  });
}
