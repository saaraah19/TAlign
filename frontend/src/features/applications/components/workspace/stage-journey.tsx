import { APPLICATION_STATUS_LABELS, type ApplicationStatus } from "../../types";

const STAGES: ApplicationStatus[] = ["applied", "screening", "interview", "offer", "hired"];

function CheckIcon() {
  return (
    <svg viewBox="0 0 12 12" className="h-2.5 w-2.5" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M2.5 6.5l2.2 2.2L9.5 3.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

/**
 * Where this candidate is in the pipeline. Deliberately shows *only*
 * the current stage and the path ahead — no per-stage dates — because
 * the backend stores the current status, not a history of transitions.
 * Dates for real events live in the activity feed instead.
 */
export function StageJourney({ status }: { status: ApplicationStatus }) {
  if (status === "rejected") {
    return (
      <div className="rounded-md bg-red-50 px-3 py-2.5">
        <p className="text-sm font-medium text-red-700">Application rejected</p>
        <p className="mt-0.5 text-xs text-red-600/80">This candidate is no longer in the pipeline.</p>
      </div>
    );
  }

  const currentIndex = STAGES.indexOf(status);

  return (
    <ol className="flex flex-col">
      {STAGES.map((stage, i) => {
        const done = i < currentIndex || (stage === "hired" && status === "hired");
        const current = i === currentIndex && status !== "hired";
        const isLast = i === STAGES.length - 1;

        return (
          <li key={stage} className="flex gap-3">
            <div className="flex flex-col items-center">
              <span
                className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full border text-white ${
                  done
                    ? "border-ink bg-ink"
                    : current
                      ? "border-accent bg-white ring-4 ring-accent/15"
                      : "border-line bg-white"
                }`}
              >
                {done ? (
                  <CheckIcon />
                ) : current ? (
                  <span className="h-1.5 w-1.5 rounded-full bg-accent" />
                ) : null}
              </span>
              {!isLast && (
                <span className={`my-1 w-px flex-1 ${done ? "bg-ink" : "bg-line"}`} />
              )}
            </div>
            <div className={`pb-4 ${isLast ? "pb-0" : ""}`}>
              <p
                className={`text-sm leading-5 ${
                  current ? "font-medium text-ink" : done ? "text-ink/70" : "text-ink/35"
                }`}
              >
                {APPLICATION_STATUS_LABELS[stage]}
              </p>
              {current && <p className="text-xs text-accent-dim">Current stage</p>}
            </div>
          </li>
        );
      })}
    </ol>
  );
}
