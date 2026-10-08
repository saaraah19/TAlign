/**
 * "2 hours ago" style formatting for activity feeds. Falls back to a
 * plain date once something is more than a week old -- a relative
 * time longer than that stops being useful ("47 days ago" tells you
 * less than the actual date would).
 */
export function formatRelativeTime(isoDate: string): string {
  const date = new Date(isoDate);
  const seconds = Math.round((date.getTime() - Date.now()) / 1000);
  const absSeconds = Math.abs(seconds);

  if (absSeconds < 60) return "Just now";

  const rtf = new Intl.RelativeTimeFormat("en", { numeric: "auto" });
  const units: [Intl.RelativeTimeFormatUnit, number][] = [
    ["day", 86400],
    ["hour", 3600],
    ["minute", 60],
  ];

  if (absSeconds >= 604_800) {
    return date.toLocaleDateString();
  }

  for (const [unit, secondsInUnit] of units) {
    if (absSeconds >= secondsInUnit) {
      return rtf.format(Math.round(seconds / secondsInUnit), unit);
    }
  }
  return "Just now";
}
