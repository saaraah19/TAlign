import { CommunicationIcon, KnowledgeIcon, ResumeIcon } from "./capability-icons";

const CAPABILITIES = [
  {
    Icon: ResumeIcon,
    title: "Resume Intelligence",
    blurb: "Reads every resume and scores fit against the job — with the reasoning shown, not a bare number.",
    example: { kind: "score", label: "94% match", detail: "Python · Docker · Leadership" },
  },
  {
    Icon: KnowledgeIcon,
    title: "Knowledge Agent",
    blurb: "Answers company and policy questions, grounded in your own documents — always with a citation.",
    example: {
      kind: "quote",
      label: "“You have 18 leave days remaining.”",
      detail: "Leave Policy, p.2",
    },
  },
  {
    Icon: CommunicationIcon,
    title: "Communication Agent",
    blurb: "Drafts interview invitations, rejections, and onboarding emails — a human reviews and sends every one.",
    example: {
      kind: "draft",
      label: "Interview invitation",
      detail: "Backend Engineer · Draft",
    },
  },
];

export function CapabilitiesSection() {
  return (
    <section id="capabilities" className="border-b border-line bg-white">
      <div className="mx-auto max-w-content px-6 py-24 sm:px-8">
        <div className="max-w-lg">
          <h2 className="text-3xl font-semibold tracking-tight text-ink">
            Three specialists. One assistant.
          </h2>
          <p className="mt-3 text-base text-ink/60">
            Your team never picks an agent — they ask Compass, and Compass routes the
            request to whichever specialist actually handles it.
          </p>
        </div>

        <div className="relative mt-16 grid gap-10 sm:grid-cols-3 sm:gap-6">
          {/* Connecting thread — desktop only, sits behind the icon tiles */}
          <div className="pointer-events-none absolute left-0 right-0 top-6 hidden h-px bg-line sm:block" />

          {CAPABILITIES.map(({ Icon, title, blurb, example }) => (
            <div key={title} className="relative">
              <div className="relative z-10 flex h-12 w-12 items-center justify-center rounded-lg border border-line bg-paper text-ink">
                <Icon className="h-6 w-6" />
              </div>
              <h3 className="mt-5 text-base font-semibold text-ink">{title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-ink/60">{blurb}</p>

              <div className="mt-4 inline-flex items-center gap-2 rounded-md border border-line bg-paper px-3 py-2">
                <span className="text-sm font-medium text-ink">{example.label}</span>
                <span className="text-xs text-ink/40">·&nbsp;{example.detail}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
