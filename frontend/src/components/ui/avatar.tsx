/**
 * Talign design system — Avatar.
 *
 * Initials only — no photo uploads exist anywhere in this product, so
 * there's nothing to ever fall back FROM. Size is a literal pixel
 * scale (not a t-shirt-size enum) since the two current call sites
 * (NavBar's 28px, Kanban cards' 32px) don't share a design-system-wide
 * scale yet; revisit if a third size shows up.
 */
export function Avatar({
  firstName,
  lastName,
  size = 28,
}: {
  firstName: string;
  lastName: string;
  size?: number;
}) {
  const initials = `${firstName[0] ?? ""}${lastName[0] ?? ""}`.toUpperCase();
  return (
    <span
      style={{ width: size, height: size, fontSize: size * 0.4 }}
      className="flex shrink-0 items-center justify-center rounded-full bg-ink font-medium text-white"
    >
      {initials}
    </span>
  );
}
