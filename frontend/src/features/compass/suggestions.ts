/**
 * Starter questions for Compass. Fixed text, never generated data, and
 * every one is something Compass can actually answer in that context —
 * a suggestion that promised more than the capability delivers would be
 * worse than none. Kept in one place because both the candidate page
 * and the global command panel offer the same ones.
 */

// Staff, on a candidate: Compass explains the stored Resume
// Intelligence analysis (the `explain_analysis` capability) and nothing
// else. Interview-question generation belongs to the V2 Interview Agent.
export const ANALYSIS_SUGGESTIONS = [
  "Why this score?",
  "What are this candidate's biggest gaps?",
  "Which required skills are missing?",
];

// A candidate, on their own application: Compass reports the pipeline
// stage (the `application_status` capability).
export const CANDIDATE_APPLICATION_SUGGESTIONS = ["What stage is my application at?"];

/** Company questions built from real, ready document titles, so each is answerable. */
export function policySuggestions(titles: string[], max = 3): string[] {
  return titles.slice(0, max).map((title) => `What does “${title}” cover?`);
}
