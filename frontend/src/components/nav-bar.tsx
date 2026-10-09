"use client";

import type { Route } from "next";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";
import { AIMark } from "@/components/ui/ai-mark";
import { useCompassPanel } from "@/components/compass-panel";
import { Avatar } from "@/components/ui/avatar";
import { useAuth } from "@/features/auth";
import { isPlainEmployee } from "@/lib/roles";

interface NavLink {
  href: Route;
  label: string;
}

const BASE_INTERNAL_LINKS: NavLink[] = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/jobs", label: "Jobs" },
  { href: "/pipeline", label: "Pipeline" },
  { href: "/knowledge", label: "Knowledge" },
];

// A plain employee (hired via HireCandidateWorkflow's portal-access
// step — see AuthService.convert_candidate_to_employee) has no
// business seeing Jobs/Pipeline, recruiting-only pages. This is the
// third branch previously flagged as missing in the 9c scope note —
// built now alongside the hire-time account conversion that finally
// makes an employee-role login possible to reach in the first place.
const EMPLOYEE_LINKS: NavLink[] = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/knowledge", label: "Knowledge" },
  { href: "/portal/leave", label: "Leave" },
];

// Shown in addition to BASE_INTERNAL_LINKS, only for roles that can act
// on the approval queue (see LeaveRequestService's module docstring —
// approval is company-wide, any ADMIN or HIRING_MANAGER, not routed to
// an individual manager). A plain recruiter role has no access to
// these endpoints, so no point showing the link.
const LEAVE_APPROVAL_LINK: NavLink = { href: "/leave-requests", label: "Leave requests" };
const RECRUITING_ROLES = ["admin", "recruiter", "hiring_manager"];
const LEAVE_APPROVAL_ROLES = ["admin", "hiring_manager"];

const CANDIDATE_LINKS: NavLink[] = [
  { href: "/dashboard", label: "Home" },
  { href: "/applications", label: "My applications" },
  { href: "/careers", label: "Browse jobs" },
];

/**
 * Persistent navigation shell for every page under (protected) -- see
 * (protected)/layout.tsx. Kept as a top nav rather than a sidebar for
 * this design pass — Sarah's brief asked to keep the existing
 * structure's simplicity while elevating it visually; a sidebar
 * remains an easy follow-up if the elevated top nav still doesn't feel
 * right once seen live.
 */
export function NavBar() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const compass = useCompassPanel();

  if (!user) return null;

  const isRecruitingRole = user.roles.some((role) => RECRUITING_ROLES.includes(role));
  const plainEmployee = isPlainEmployee(user.roles);

  const links =
    user.account_type === "candidate"
      ? CANDIDATE_LINKS
      : plainEmployee
        ? EMPLOYEE_LINKS
        : LEAVE_APPROVAL_ROLES.some((role) => user.roles.includes(role))
          ? [...BASE_INTERNAL_LINKS, LEAVE_APPROVAL_LINK]
          : BASE_INTERNAL_LINKS;

  async function handleLogout() {
    await logout();
    router.push("/login");
  }

  return (
    <nav className="sticky top-0 z-40 border-b border-line bg-paper/90 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-content items-center justify-between px-6 sm:px-8">
        <Link href="/dashboard" className="flex items-center gap-2">
          <AIMark className="h-4 w-4 text-accent" />
          <span className="text-sm font-semibold tracking-tight text-ink">TALIGN</span>
        </Link>

        {/* Desktop links */}
        <div className="hidden items-center gap-1 sm:flex">
          {links.map((link) => {
            const active = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                  active ? "bg-ink/[0.06] text-ink" : "text-ink/55 hover:text-ink"
                }`}
              >
                {link.label}
              </Link>
            );
          })}
        </div>

        <div className="hidden items-center gap-3 sm:flex">
          {compass.canAsk && (
            <button
              type="button"
              onClick={compass.open}
              className="flex items-center gap-2 rounded-md border border-line bg-white px-3 py-1.5 text-xs font-medium text-ink/70 transition-colors hover:border-ink/30 hover:text-ink"
            >
              <AIMark className="h-3.5 w-3.5 text-accent" />
              Ask Compass
              <kbd className="rounded border border-line px-1.5 py-0.5 text-[10px] text-ink/40">
                {compass.shortcutLabel}
              </kbd>
            </button>
          )}
          <div className="flex items-center gap-2 border-l border-line pl-3">
            <Avatar firstName={user.first_name} lastName={user.last_name} />
            <span className="text-sm text-ink/60">{user.first_name}</span>
          </div>
          <button
            onClick={handleLogout}
            className="rounded-md border border-line px-3 py-1.5 text-xs font-medium text-ink/70 transition-colors hover:border-ink/30 hover:text-ink"
          >
            Sign out
          </button>
        </div>

        {/* Mobile toggle */}
        <button
          onClick={() => setMobileOpen((open) => !open)}
          aria-label={mobileOpen ? "Close menu" : "Open menu"}
          aria-expanded={mobileOpen}
          className="text-ink sm:hidden"
        >
          <svg
            width="22"
            height="22"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.75"
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
        <div className="flex flex-col gap-1 border-t border-line px-6 py-3 sm:hidden">
          {links.map((link) => {
            const active = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setMobileOpen(false)}
                className={`rounded-md px-2 py-2 text-sm font-medium ${
                  active ? "bg-ink/[0.06] text-ink" : "text-ink/55"
                }`}
              >
                {link.label}
              </Link>
            );
          })}
          {compass.canAsk && (
            <button
              type="button"
              onClick={() => {
                setMobileOpen(false);
                compass.open();
              }}
              className="flex items-center gap-2 rounded-md px-2 py-2 text-sm font-medium text-ink/55"
            >
              <AIMark className="h-3.5 w-3.5 text-accent" />
              Ask Compass
            </button>
          )}
          <div className="mt-2 flex items-center justify-between border-t border-line pt-3">
            <div className="flex items-center gap-2">
              <Avatar firstName={user.first_name} lastName={user.last_name} />
              <span className="text-sm text-ink/60">{user.first_name}</span>
            </div>
            <button
              onClick={handleLogout}
              className="rounded-md border border-line px-3 py-1.5 text-xs font-medium text-ink/70"
            >
              Sign out
            </button>
          </div>
        </div>
      )}
    </nav>
  );
}
