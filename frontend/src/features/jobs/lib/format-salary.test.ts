import { describe, expect, it } from "vitest";
import { formatSalaryRange } from "./format-salary";

const job = (min: number | null, max: number | null, currency: "USD" | "EUR" | "GBP" | "CAD" = "USD") => ({
  salary_min: min,
  salary_max: max,
  salary_currency: currency,
});

describe("formatSalaryRange", () => {
  it("writes a range with thousands separators", () => {
    expect(formatSalaryRange(job(60000, 80000))).toBe("$60,000 – $80,000");
  });

  it("handles a minimum only", () => {
    expect(formatSalaryRange(job(50000, null, "EUR"))).toBe("From €50,000");
  });

  it("handles a maximum only", () => {
    expect(formatSalaryRange(job(null, 90000, "GBP"))).toBe("Up to £90,000");
  });

  it("returns null when no salary is stated", () => {
    expect(formatSalaryRange(job(null, null))).toBeNull();
  });

  it("treats zero as a real value, not as missing", () => {
    expect(formatSalaryRange(job(0, 0))).toBe("$0 – $0");
  });

  it("labels Canadian dollars distinctly", () => {
    expect(formatSalaryRange(job(1000, null, "CAD"))).toBe("From CA$1,000");
  });
});
