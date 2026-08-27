"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "@/features/auth";
import { NavBar } from "@/components/nav-bar";

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
    return <main className="p-8 text-sm text-gray-500">Loading…</main>;
  }

  return (
    <>
      <NavBar />
      {children}
    </>
  );
}
