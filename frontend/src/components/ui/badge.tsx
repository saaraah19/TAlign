/**
 * Talign design system — Badge.
 *
 * A small status pill. Built in Phase 4 because three different places
 * (email draft/sent state, experience-fit verdict, workflow outcome)
 * needed the same shape with different meaning. `tone` carries the
 * meaning, never the call site's own colors, so "success" always looks
 * the same everywhere.
 */
type Tone = "neutral" | "success" | "warning" | "danger" | "info";

const TONE_CLASSES: Record<Tone, string> = {
  neutral: "bg-ink/[0.06] text-ink/70",
  success: "bg-emerald-50 text-emerald-700",
  warning: "bg-amber-50 text-amber-700",
  danger: "bg-red-50 text-red-600",
  info: "bg-blue-50 text-blue-700",
};

export function Badge({
  tone = "neutral",
  children,
}: {
  tone?: Tone;
  children: React.ReactNode;
}) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${TONE_CLASSES[tone]}`}
    >
      {children}
    </span>
  );
}
