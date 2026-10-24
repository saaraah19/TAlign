"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { AIMark } from "@/components/ui/ai-mark";
import { Avatar } from "@/components/ui/avatar";
import { buttonClasses } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/features/auth";

/**
 * The header for the public part of the site (the job board and the
 * apply flow). These pages used to have no header at all: no logo, no
 * way to sign in, and a logged-in candidate lost all navigation the
 * moment they opened /careers. It adapts to who is looking — a
 * visitor sees sign-in and sign-up, a signed-in person sees a way
 * back to their own space — and never blocks the page on auth state.
 */
export function PublicHeader() {
  const { user, isLoading } = useAuth();
  const pathname = usePathname();
  const onJobBoard = pathname.startsWith("/careers");

  const isCandidate = user?.account_type === "candidate";
  const homeHref = isCandidate ? "/applications" : "/dashboard";
  const homeLabel = isCandidate ? "My applications" : "Dashboard";

  return (
    <header className="sticky top-0 z-40 border-b border-line bg-paper/90 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-content items-center justify-between px-6 sm:px-8">
        <div className="flex items-center gap-8">
          <Link href="/" className="flex items-center gap-2">
            <AIMark className="h-4 w-4 text-accent" />
            <span className="text-sm font-semibold tracking-tight text-ink">TALIGN</span>
          </Link>
          <Link
            href="/careers"
            className={`hidden rounded-md px-3 py-1.5 text-sm font-medium transition-colors sm:block ${
              onJobBoard ? "bg-ink/[0.06] text-ink" : "text-ink/55 hover:text-ink"
            }`}
          >
            Open positions
          </Link>
        </div>

        <div className="flex items-center gap-3">
          {isLoading ? (
            <Skeleton className="h-8 w-32" />
          ) : user ? (
            <>
              <Link href={homeHref} className={buttonClasses("secondary", "sm")}>
                {homeLabel}
              </Link>
              <span className="hidden sm:block">
                <Avatar firstName={user.first_name} lastName={user.last_name} />
              </span>
            </>
          ) : (
            <>
              <Link href="/login" className="text-sm font-medium text-ink/70 hover:text-ink">
                Sign in
              </Link>
              <Link href="/register/candidate" className={buttonClasses("primary", "sm")}>
                Create account
              </Link>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
