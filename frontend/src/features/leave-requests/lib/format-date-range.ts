// Backend dates are plain "YYYY-MM-DD" strings. Parsing them with
// `new Date(str)` reads them as UTC midnight, which shows the previous
// day for anyone behind UTC. A date-time string with no "Z" is read as
// local time, so appending a midnight time keeps the calendar day intact.
function parseLocalDate(iso: string): Date {
  return new Date(`${iso.slice(0, 10)}T00:00:00`);
}

/** Inclusive calendar days — the same formula the backend uses for leave balance. */
export function leaveDayCount(start: string, end: string): number {
  const ms = parseLocalDate(end).getTime() - parseLocalDate(start).getTime();
  return Math.round(ms / 86_400_000) + 1;
}

/** "Oct 14 – Oct 18, 2026" (year shown once when both dates share it). */
export function formatDateRange(start: string, end: string): string {
  const s = parseLocalDate(start);
  const e = parseLocalDate(end);
  const sameYear = s.getFullYear() === e.getFullYear();
  const withYear: Intl.DateTimeFormatOptions = { month: "short", day: "numeric", year: "numeric" };
  const noYear: Intl.DateTimeFormatOptions = { month: "short", day: "numeric" };
  const startText = s.toLocaleDateString("en", sameYear ? noYear : withYear);
  const endText = e.toLocaleDateString("en", withYear);
  return start.slice(0, 10) === end.slice(0, 10) ? endText : `${startText} – ${endText}`;
}
