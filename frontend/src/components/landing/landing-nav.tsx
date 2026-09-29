"use client";

import Link from "next/link";

/**
 * "Product" / "For Candidates" / "For Companies" / "About" are anchors
 * into this same single-page site, not separate marketing pages — this
 * is a portfolio project's landing page, not a multi-page CMS site, so
 * pointing them at real routes that don't exist would ship dead links.
 * "Jobs" is the one genuinely real destination (the public job board),
 * so it's an actual route.
 */
const SECTION_LINKS = [
  { href: "#compass", label: "Product" },
  { href: "#journey", label: "For Candidates" },
  { href: "#capabilities", label: "For Companies" },
  { href: "#trust", label: "About" },
];

export function LandingNav() {
  return (
    <header className="sticky top-0 z-40 border-b border-line bg-paper/80 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-content items-center justify-between px-6 sm:px-8">
        <Link href="/" className="text-[15px] font-semibold tracking-tight text-ink">
          TALIGN
        </Link>

        <nav className="hidden items-center gap-8 md:flex">
          {SECTION_LINKS.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="text-sm text-ink/60 transition-colors hover:text-ink"
            >
              {link.label}
            </a>
          ))}
          <Link href="/careers" className="text-sm text-ink/60 transition-colors hover:text-ink">
            Jobs
          </Link>
        </nav>

        <div className="flex items-center gap-3">
          <Link href="/login" className="text-sm font-medium text-ink/70 hover:text-ink">
            Sign in
          </Link>
          <Link
            href="/register/company"
            className="rounded-md bg-ink px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-ink-700"
          >
            Get started
          </Link>
        </div>
      </div>
    </header>
  );
}
