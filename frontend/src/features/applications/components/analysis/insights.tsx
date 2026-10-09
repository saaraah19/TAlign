function InsightList({
  title,
  items,
  dotClass,
}: {
  title: string;
  items: string[];
  dotClass: string;
}) {
  if (items.length === 0) return null;
  return (
    <div className="rounded-lg border border-line bg-white p-5">
      <p className="text-sm font-medium text-ink">{title}</p>
      <ul className="mt-3 flex flex-col gap-2.5">
        {items.map((item) => (
          <li key={item} className="flex items-start gap-2.5 text-sm leading-relaxed text-ink/70">
            <span className={`mt-2 h-1.5 w-1.5 shrink-0 rounded-full ${dotClass}`} />
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}

/** Strengths and concerns side by side — visually distinct, equally weighted. */
export function Insights({
  strengths,
  concerns,
}: {
  strengths: string[];
  concerns: string[];
}) {
  if (strengths.length === 0 && concerns.length === 0) return null;
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <InsightList title="Strengths" items={strengths} dotClass="bg-emerald-500" />
      <InsightList title="Potential concerns" items={concerns} dotClass="bg-amber-500" />
    </div>
  );
}
