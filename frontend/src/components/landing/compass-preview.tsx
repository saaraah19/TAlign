/**
 * Static visual mock of the Compass chat interface — the hero's visual
 * anchor. Deliberately NOT wired to the real /compass/ask endpoint:
 * this is marketing content for a logged-out visitor, not a working
 * product surface, so it always renders the same considered example
 * rather than depending on a backend being reachable at all.
 */
const CANDIDATES = [
  { name: "Sarah B.", role: "5 yrs · Python, Airflow", match: 94 },
  { name: "Amine K.", role: "3 yrs · SQL, dbt", match: 91 },
  { name: "Lina T.", role: "4 yrs · Python, Looker", match: 86 },
];

export function CompassPreview() {
  return (
    <div className="relative">
      <div className="pointer-events-none absolute -inset-6 -z-10 rounded-[2rem] bg-accent/10 blur-2xl" />
      <div className="overflow-hidden rounded-xl border border-white/10 bg-ink shadow-2xl shadow-black/40">
        {/* Window chrome */}
        <div className="flex items-center justify-between border-b border-white/10 px-5 py-3.5">
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full border border-accent">
              <span className="block h-full w-full scale-50 rounded-full bg-accent" />
            </span>
            <span className="text-sm font-medium text-white">Compass</span>
          </div>
          <span className="text-[11px] text-white/40">Data Analyst · Talent Analytics</span>
        </div>

        {/* Question */}
        <div className="space-y-4 px-5 pt-5">
          <div className="ml-auto max-w-[85%] rounded-lg rounded-tr-sm bg-white/[0.07] px-3.5 py-2.5 text-sm text-white/90">
            Show me candidates for the Data Analyst role
          </div>

          {/* Answer */}
          <div className="max-w-[92%] rounded-lg rounded-tl-sm bg-white/[0.04] px-3.5 py-3 text-sm text-white/70">
            12 matching candidates, ranked by alignment with the role&apos;s requirements.
          </div>
        </div>

        {/* Candidate list */}
        <div className="mt-1 divide-y divide-white/[0.06] px-5">
          {CANDIDATES.map((c) => (
            <div key={c.name} className="flex items-center justify-between py-3">
              <div>
                <p className="text-sm font-medium text-white">{c.name}</p>
                <p className="text-xs text-white/40">{c.role}</p>
              </div>
              <span className="font-mono text-sm font-medium text-accent-light">
                {c.match}%
              </span>
            </div>
          ))}
        </div>

        {/* Input bar */}
        <div className="border-t border-white/10 p-4">
          <div className="flex items-center gap-2 rounded-md border border-white/10 bg-white/[0.03] px-3 py-2.5">
            <span className="text-sm text-white/30">Ask Compass anything…</span>
          </div>
        </div>
      </div>
    </div>
  );
}
