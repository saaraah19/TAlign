/**
 * The recognizable Compass/AI glyph — used everywhere Compass shows up
 * (dashboard briefing, Knowledge's "Ask Compass", candidate assessment,
 * the future command panel) so the brand reads as one system, not text
 * that happens to say "Compass." Same line-art language as
 * app/icon.svg and capability-icons.tsx: thin stroke, no fill except a
 * small accent core.
 */
export function AIMark({ className = "h-4 w-4" }: { className?: string }) {
  return (
    <svg viewBox="0 0 16 16" fill="none" className={className}>
      <path
        d="M8 1.5c.4 2.3 1.2 3.1 3.5 3.5-2.3.4-3.1 1.2-3.5 3.5-.4-2.3-1.2-3.1-3.5-3.5C6.8 4.6 7.6 3.8 8 1.5z"
        fill="currentColor"
      />
      <path
        d="M12.5 9.5c.2 1.1.6 1.5 1.7 1.7-1.1.2-1.5.6-1.7 1.7-.2-1.1-.6-1.5-1.7-1.7 1.1-.2 1.5-.6 1.7-1.7z"
        fill="currentColor"
        opacity="0.6"
      />
    </svg>
  );
}
