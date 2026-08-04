import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { communicationApi } from "../api";
import type { EmailType } from "../types";

const emailsKey = (applicationId: string) => ["applications", applicationId, "emails"] as const;

export function useEmails(applicationId: string) {
  return useQuery({
    queryKey: emailsKey(applicationId),
    queryFn: () => communicationApi.list(applicationId),
    enabled: Boolean(applicationId),
  });
}

// Every mutation below invalidates onSettled (success AND error), not
// just onSuccess — applying the lesson from the Job transition bug:
// if the client-perceived outcome and the real server outcome ever
// disagree for any reason, the UI still re-syncs automatically within
// a second instead of needing a manual refresh.

export function useDraftEmail(applicationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (emailType: EmailType) => communicationApi.draft(applicationId, emailType),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: emailsKey(applicationId) });
    },
  });
}

export function useRegenerateEmail(applicationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (emailId: string) => communicationApi.regenerate(applicationId, emailId),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: emailsKey(applicationId) });
    },
  });
}

export function useUpdateEmail(applicationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      emailId,
      subject,
      body,
    }: {
      emailId: string;
      subject: string;
      body: string;
    }) => communicationApi.update(applicationId, emailId, subject, body),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: emailsKey(applicationId) });
    },
  });
}

export function useSendEmail(applicationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (emailId: string) => communicationApi.send(applicationId, emailId),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: emailsKey(applicationId) });
    },
  });
}
