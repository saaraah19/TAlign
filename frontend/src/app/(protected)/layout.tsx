"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "@/features/auth";
import { CompassPanelProvider } from "@/components/compass-panel";
import { NavBar } from "@/components/nav-bar";
import { Skeleton } from "@/components/ui/skeleton";

/**
 * Shared shell for every route under (protected). Two things this
 * centralizes that were previously duplicated (inconsistently -- some
 * pages had it, jobs/[id] had none at all) on every single page:
 * the auth guard (redirect to /login if not authenticated) and now,
 * for the first time, a persistent navigation bar with a working sign-
 * out button reachable from anywhere in the app.
 *
 * Individual pages no longer need their own `useAuth` + redirect
 * effect -- by the time a page's children render here, `user` is
 * guaranteed non-null. Pages that still read `useAuth()` for
 * role-specific rendering (e.g. "canCreate" checks) continue to do so;
 * only the loading/redirect boilerplate moves up here.
 */
export default function ProtectedLayout({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !user) router.replace("/login");
  }, [isLoading, user, router]);

  if (isLoading || !user) {
    return (
      <main className="min-h-screen bg-paper">
        <div className="mx-auto max-w-content px-6 py-5 sm:px-8">
          <Skeleton className="h-6 w-28" />
          <Skeleton className="mt-12 h-9 w-72" />
          <Skeleton className="mt-8 h-64 w-full" />
        </div>
      </main>
    );
  }

  return (
    <CompassPanelProvider>
      <div className="min-h-screen bg-paper">
        <NavBar />
        {children}
      </div>
    </CompassPanelProvider>
  );
}
