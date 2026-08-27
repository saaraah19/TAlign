"use client";

import type { Route } from "next";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";
import { useAuth } from "@/features/auth";

interface NavLink {
  href: Route;
  label: string;
}

const INTERNAL_LINKS: NavLink[] = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/jobs", label: "Jobs" },
  { href: "/pipeline", label: "Pipeline" },
  { href: "/knowledge", label: "Knowledge" },
];

const CANDIDATE_LINKS: NavLink[] = [
  { href: "/dashboard", label: "Home" },
  { href: "/applications", label: "My applications" },
  { href: "/careers", label: "Browse jobs" },
];

/**
 * Persistent navigation shell for every page under (protected) -- see
 * (protected)/layout.tsx. Before this, no shared layout existed at all:
 * every page hand-rolled its own auth guard, and only the Dashboard
 * page had a way to sign out. Every other page was a dead end you
 * could only leave via the browser's back button.
 */
export function NavBar() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  if (!user) return null;

  const links = user.account_type === "candidate" ? CANDIDATE_LINKS : INTERNAL_LINKS;

  async function handleLogout() {
    await logout();
    router.push("/login");
  }

  return (
    <nav className="border-b border-gray-200">
      <div className="mx-auto flex max-w-4xl items-center justify-between px-6 py-3">
        <Link href="/dashboard" className="text-sm font-semibold text-gray-900">
          Talign
        </Link>

        {/* Desktop links */}
        <div className="hidden items-center gap-6 sm:flex">
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={
                pathname === link.href
                  ? "text-sm font-medium text-gray-900"
                  : "text-sm font-medium text-gray-500 hover:text-gray-900"
              }
            >
              {link.label}
            </Link>
          ))}
          <button
            onClick={handleLogout}
            className="rounded-md border border-gray-300 px-3 py-1.5 text-xs font-medium"
          >
            Sign out
          </button>
        </div>

        {/* Mobile toggle */}
        <button
          onClick={() => setMobileOpen((open) => !open)}
          aria-label={mobileOpen ? "Close menu" : "Open menu"}
          aria-expanded={mobileOpen}
          className="sm:hidden"
        >
          <svg
            width="22"
            height="22"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
          >
            {mobileOpen ? (
              <path d="M6 6l12 12M18 6L6 18" />
            ) : (
              <path d="M4 7h16M4 12h16M4 17h16" />
            )}
          </svg>
        </button>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="flex flex-col gap-1 border-t border-gray-200 px-6 py-3 sm:hidden">
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              onClick={() => setMobileOpen(false)}
              className={
                pathname === link.href
                  ? "py-2 text-sm font-medium text-gray-900"
                  : "py-2 text-sm font-medium text-gray-500"
              }
            >
              {link.label}
            </Link>
          ))}
          <button
            onClick={handleLogout}
            className="mt-2 rounded-md border border-gray-300 px-3 py-1.5 text-left text-xs font-medium"
          >
            Sign out
          </button>
        </div>
      )}
    </nav>
  );
}
