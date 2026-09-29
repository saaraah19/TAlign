import Link from "next/link";
import { CompassPreview } from "./compass-preview";

export function HeroSection() {
  return (
    <section id="compass" className="border-b border-line bg-paper">
      <div className="mx-auto grid max-w-content items-center gap-16 px-6 py-20 sm:px-8 sm:py-28 lg:grid-cols-[1.05fr_1fr] lg:gap-12">
        <div className="animate-fade-up">
          <h1 className="max-w-lg text-[2.75rem] font-semibold leading-[1.08] tracking-tight text-ink sm:text-5xl">
            The talent platform that thinks, so your team can decide.
          </h1>
          <p className="mt-6 max-w-md text-lg leading-relaxed text-ink/60">
            Compass screens resumes, answers policy questions, and drafts every
            email your hiring process needs — in one workspace, under one
            assistant. It recommends. Your team decides.
          </p>
          <div className="mt-9 flex flex-wrap items-center gap-4">
            <Link
              href="/register/company"
              className="rounded-md bg-ink px-6 py-3 text-sm font-medium text-white transition-colors hover:bg-ink-700"
            >
              Get started
            </Link>
            <Link
              href="/careers"
              className="text-sm font-medium text-ink/70 underline decoration-line underline-offset-4 transition-colors hover:text-ink"
            >
              Browse open jobs
            </Link>
          </div>
        </div>

        <div className="animate-fade-up [animation-delay:120ms] [animation-fill-mode:both]">
          <CompassPreview />
        </div>
      </div>
    </section>
  );
}
