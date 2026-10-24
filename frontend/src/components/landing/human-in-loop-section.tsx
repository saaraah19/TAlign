const AI_VERBS = ["Analyzes resumes", "Drafts emails", "Summarizes candidates", "Answers policy questions"];
const HUMAN_VERBS = ["Reviews every draft", "Decides who moves forward", "Approves every hire", "Approves every leave request"];

export function HumanInLoopSection() {
  return (
    <section id="trust" className="border-b border-line bg-white">
      <div className="mx-auto max-w-content px-6 py-24 sm:px-8">
        <h2 className="max-w-xl text-3xl font-semibold tracking-tight text-ink">
          AI handles the busywork. Humans make the decisions.
        </h2>

        <div className="mt-14 grid overflow-hidden rounded-xl border border-line sm:grid-cols-2">
          <div className="border-b border-line p-8 sm:border-b-0 sm:border-r">
            <p className="text-xs font-medium uppercase tracking-wide text-ink/40">AI</p>
            <ul className="mt-5 space-y-3.5">
              {AI_VERBS.map((v) => (
                <li key={v} className="text-sm text-ink/60">
                  {v}
                </li>
              ))}
            </ul>
          </div>

          <div className="bg-accent/[0.05] p-8">
            <p className="text-xs font-medium uppercase tracking-wide text-accent-dim">Human</p>
            <ul className="mt-5 space-y-3.5">
              {HUMAN_VERBS.map((v) => (
                <li key={v} className="text-sm font-medium text-ink">
                  {v}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}
