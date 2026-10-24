/**
 * Talign design system — Skeleton.
 *
 * A pulsing placeholder shaped like the content that is about to
 * arrive. Replaces bare "Loading…" text, which tells the user nothing
 * about what is coming and makes the page jump when it lands. Size it
 * with `className` (e.g. "h-20 w-full") to match the real thing.
 * The pulse stops for people who ask their OS for reduced motion.
 */
export function Skeleton({ className = "" }: { className?: string }) {
  return (
    <div
      aria-hidden="true"
      className={`animate-pulse rounded-md bg-ink/[0.06] motion-reduce:animate-none ${className}`}
    />
  );
}
