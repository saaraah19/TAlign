import Link from "next/link";
import { CompassPreview } from "@/components/landing/compass-preview";
import { AIMark } from "@/components/ui/ai-mark";

/**
 * Shared shell for every unauthenticated auth screen (login, both
 * registration flows) — the left brand panel is identical across all
 * three, so it lives here once rather than being copy-pasted per page.
 * Reuses the exact same CompassPreview component the landing page's
 * hero uses (not a re-styled copy) — this is the literal mechanism by
 * which the authenticated app shares one visual identity with the
 * marketing site, not just similar-looking colors.
 */
export function AuthSplitLayout({
  eyebrow,
  children,
}: {
  eyebrow: string;
  children: React.ReactNode;
}) {
  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      {/* Left — brand panel, hidden on small screens to keep the form the focus on mobile */}
      <div className="relative hidden flex-col justify-between overflow-hidden bg-ink px-12 py-12 lg:flex">
        <Link href="/" className="flex items-center gap-2 text-white">
          <AIMark className="h-4 w-4 text-accent-light" />
          <span className="text-sm font-semibold tracking-tight">TALIGN</span>
        </Link>

        <div>
          <p className="max-w-sm text-2xl font-semibold leading-snug tracking-tight text-white">
            One assistant. Every hiring decision still stays with your team.
          </p>
          <div className="mt-10 max-w-sm">
            <CompassPreview />
          </div>
        </div>

        <p className="text-xs text-white/30">{eyebrow}</p>
      </div>

      {/* Right — the actual form */}
      <div className="flex flex-col justify-center px-6 py-16 sm:px-12 lg:px-20">
        <div className="mx-auto w-full max-w-sm">
          <Link href="/" className="mb-10 flex items-center gap-2 lg:hidden">
            <AIMark className="h-4 w-4 text-accent" />
            <span className="text-sm font-semibold tracking-tight text-ink">TALIGN</span>
          </Link>
          {children}
        </div>
      </div>
    </div>
  );
}
