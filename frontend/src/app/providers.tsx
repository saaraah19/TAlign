"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState, type ReactNode } from "react";
import { BackendWakeGate } from "@/components/backend-wake-gate";
import { ToastProvider } from "@/components/ui/toast";
import { AuthProvider } from "@/features/auth";

export function Providers({ children }: { children: ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: { queries: { retry: 1, staleTime: 30_000 } },
      }),
  );

  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <ToastProvider>{children}</ToastProvider>
        <BackendWakeGate />
      </AuthProvider>
    </QueryClientProvider>
  );
}
