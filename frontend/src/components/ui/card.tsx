/**
 * Talign design system — Card.
 *
 * The one "surface" container used throughout the authenticated app:
 * white on the app's tinted `paper` background (see (protected)/layout.tsx),
 * a hairline border rather than a shadow (shadows are reserved for truly
 * elevated things — the Compass mockup, modals/dropdowns later — a
 * shadow under every card is exactly the generic-SaaS tell the redesign
 * brief calls out).
 */
export function Card({
  className = "",
  children,
}: {
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <div className={`rounded-lg border border-line bg-white ${className}`}>{children}</div>
  );
}
