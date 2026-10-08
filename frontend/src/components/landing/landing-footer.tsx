import type { Route } from "next";
import Link from "next/link";

const COLUMNS: { title: string; links: { label: string; href: string }[] }[] = [
  {
    title: "Product",
    links: [
      { label: "Compass", href: "#compass" },
      { label: "Capabilities", href: "#capabilities" },
      { label: "How it works", href: "#journey" },
    ],
  },
  {
    title: "Candidates",
    links: [{ label: "Browse jobs", href: "/careers" }],
  },
  {
    title: "Companies",
    links: [{ label: "Get started", href: "/register/company" }],
  },
  {
    title: "Resources",
    links: [{ label: "Sign in", href: "/login" }],
  },
];

export function LandingFooter() {
  return (
    <footer className="bg-ink text-white/60">
      <div className="mx-auto max-w-content px-6 py-16 sm:px-8">
        <div className="grid gap-10 sm:grid-cols-5">
          <div className="sm:col-span-2">
            <p className="text-sm font-semibold tracking-tight text-white">TALIGN</p>
            <p className="mt-3 max-w-[26ch] text-sm text-white/40">
              An AI-native Talent Operating System.
            </p>
          </div>
          {COLUMNS.map((col) => (
            <div key={col.title}>
              <p className="text-xs font-medium uppercase tracking-wide text-white/30">
                {col.title}
              </p>
              <ul className="mt-4 space-y-2.5">
                {col.links.map((link) =>
                  link.href.startsWith("#") ? (
                    <li key={link.label}>
                      <a href={link.href} className="text-sm hover:text-white">
                        {link.label}
                      </a>
                    </li>
                  ) : (
                    <li key={link.label}>
                      <Link href={link.href as Route} className="text-sm hover:text-white">
                        {link.label}
                      </Link>
                    </li>
                  )
                )}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-14 flex flex-col gap-4 border-t border-white/10 pt-8 text-xs text-white/30 sm:flex-row sm:items-center sm:justify-between">
          <span>© {new Date().getFullYear()} Talign. Portfolio project — not a commercial product.</span>
          <div className="flex gap-6">
            <span>Privacy</span>
            <span>Terms</span>
            <span>Contact</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
