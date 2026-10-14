import { CURRENCY_SYMBOLS, type Job } from "../types";

/**
 * "$60,000 – $80,000", "From $60,000", "Up to $80,000", or null when
 * the job states no salary at all. One place for this so the public
 * job page, the careers list and the recruiter's view never disagree
 * about how a range is written. The currency symbol is a label only —
 * nothing here converts between currencies.
 */
export function formatSalaryRange(
  job: Pick<Job, "salary_min" | "salary_max" | "salary_currency">,
): string | null {
  const { salary_min: min, salary_max: max, salary_currency } = job;
  const symbol = CURRENCY_SYMBOLS[salary_currency];
  const money = (n: number) => `${symbol}${n.toLocaleString("en-US")}`;

  if (min !== null && max !== null) return `${money(min)} – ${money(max)}`;
  if (min !== null) return `From ${money(min)}`;
  if (max !== null) return `Up to ${money(max)}`;
  return null;
}
