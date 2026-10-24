import { AIMark } from "@/components/ui/ai-mark";
import { CompassAsk } from "@/features/compass";

/**
 * Compass as the centerpiece of the Knowledge Center: the one dark
 * surface on the page (same treatment as the Dashboard brief), with
 * the question box inside it. Suggestions are built by the parent from
 * real document titles, so every one is answerable from what's
 * actually in the library.
 */
export function CompassHero({ suggestions }: { suggestions: string[] }) {
  return (
    <section className="rounded-xl bg-ink p-6 sm:p-8">
      <div className="flex items-center gap-2">
        <AIMark className="h-4 w-4 text-accent-light" />
        <p className="text-xs font-medium uppercase tracking-wide text-white/50">Compass</p>
      </div>
      <h2 className="mt-3 text-xl font-semibold tracking-tight text-white">
        Ask anything about your company&apos;s policies
      </h2>
      <p className="mt-1.5 max-w-xl text-sm leading-relaxed text-white/55">
        Answers are drawn from the documents below, with the source passages cited so you can
        check them.
      </p>
      <div className="mt-5">
        <CompassAsk suggestions={suggestions} showHeader={false} />
      </div>
    </section>
  );
}
