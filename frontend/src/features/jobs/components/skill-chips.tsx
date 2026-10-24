/**
 * A wrapped row of skill pills. `max` keeps list cards compact: past it,
 * the rest collapse into a "+N" pill instead of growing the card.
 */
export function SkillChips({
  skills,
  max,
  className = "",
}: {
  skills: string[];
  max?: number;
  className?: string;
}) {
  if (skills.length === 0) return null;
  const shown = max === undefined ? skills : skills.slice(0, max);
  const hidden = skills.length - shown.length;

  return (
    <ul className={`flex flex-wrap gap-1.5 ${className}`}>
      {shown.map((skill) => (
        <li
          key={skill}
          className="rounded-full bg-ink/[0.05] px-2.5 py-1 text-xs font-medium text-ink/65"
        >
          {skill}
        </li>
      ))}
      {hidden > 0 && (
        <li className="rounded-full px-2 py-1 text-xs font-medium text-ink/40">+{hidden}</li>
      )}
    </ul>
  );
}
