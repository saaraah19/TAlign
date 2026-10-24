/**
 * Talign design system — EmptyState.
 *
 * Every empty list answers three questions, in this order: what is
 * missing (title), why it matters or why it is empty (description),
 * and what to do next (action). A list that is empty and says only
 * "Nothing here" leaves the person stuck; this primitive makes the
 * third part easy to include.
 */
export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description?: React.ReactNode;
  /** The next step, usually a Button or a Link. */
  action?: React.ReactNode;
}) {
  return (
    <div className="rounded-lg border border-dashed border-line px-6 py-12 text-center">
      <p className="text-sm font-medium text-ink">{title}</p>
      {description && (
        <p className="mx-auto mt-1.5 max-w-sm text-xs leading-relaxed text-ink/50">
          {description}
        </p>
      )}
      {action && <div className="mt-5 flex justify-center">{action}</div>}
    </div>
  );
}
