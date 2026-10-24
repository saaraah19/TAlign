const STEPS = [
  { n: "01", label: "Candidate", detail: "Applies to an open role" },
  { n: "02", label: "AI analysis", detail: "Resume Intelligence scores the fit" },
  { n: "03", label: "Human review", detail: "A recruiter decides, not an algorithm" },
  { n: "04", label: "Hired", detail: "One workflow: employee record, checklist, welcome email" },
  { n: "05", label: "Employee", detail: "Same login — Knowledge, Compass, leave requests" },
];

export function JourneySection() {
  return (
    <section id="journey" className="border-b border-line bg-paper">
      <div className="mx-auto max-w-content px-6 py-24 sm:px-8">
        <div className="max-w-lg">
          <h2 className="text-3xl font-semibold tracking-tight text-ink">
            One identity, two chapters.
          </h2>
          <p className="mt-3 text-base text-ink/60">
            When someone is hired, their own candidate account converts in
            place into an employee account — same email, same password.
            Nothing to re-issue, nothing to re-enter.
          </p>
        </div>

        <div className="mt-16 grid gap-10 sm:grid-cols-5 sm:gap-4">
          {STEPS.map((step, i) => {
            const isEmployeeChapter = i >= 3;
            return (
              <div key={step.n} className="relative">
                <div
                  className={`h-px w-full ${i === 0 ? "sm:hidden" : "hidden sm:block"} ${
                    isEmployeeChapter ? "bg-accent/40" : "bg-line"
                  }`}
                />
                <div className="mt-0 sm:mt-4">
                  <span
                    className={`font-mono text-xs ${
                      isEmployeeChapter ? "text-accent-dim" : "text-ink/35"
                    }`}
                  >
                    {step.n}
                  </span>
                  <p className="mt-2 text-sm font-semibold text-ink">{step.label}</p>
                  <p className="mt-1.5 text-sm leading-relaxed text-ink/55">{step.detail}</p>
                </div>
              </div>
            );
          })}
        </div>

        <p className="mt-14 inline-block rounded-md border border-accent/30 bg-accent/[0.06] px-4 py-2.5 text-sm font-medium text-accent-dim">
          Steps 04 and 05 share one account — not a second login.
        </p>
      </div>
    </section>
  );
}
