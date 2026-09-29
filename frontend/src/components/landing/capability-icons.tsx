/**
 * Hand-drawn line icons, one shared visual language (1.5px stroke,
 * rounded caps, currentColor) rather than a generic icon-library set —
 * kept bespoke and consistent with app/icon.svg's mark.
 */
export function ResumeIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 28 28" fill="none" className={className}>
      <rect x="6" y="4" width="16" height="20" rx="2" stroke="currentColor" strokeWidth="1.5" />
      <path d="M9.5 9h9M9.5 12.5h9M9.5 16h5.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      <circle cx="19" cy="20.5" r="3" fill="currentColor" fillOpacity="0.12" />
      <path d="M17.6 20.5l1 1 1.8-1.9" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function KnowledgeIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 28 28" fill="none" className={className}>
      <path
        d="M14 8c-1.6-1.3-3.7-2-6.5-2-.6 0-1 .45-1 1v12.5c0 .6.5 1 1.1 1 2.5 0 4.5.6 6 1.8M14 8c1.6-1.3 3.7-2 6.5-2 .6 0 1 .45 1 1v12.5c0 .6-.5 1-1.1 1-2.5 0-4.5.6-6 1.8M14 8v14.3"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function CommunicationIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 28 28" fill="none" className={className}>
      <path
        d="M5 8.5A2.5 2.5 0 017.5 6h13A2.5 2.5 0 0123 8.5v8a2.5 2.5 0 01-2.5 2.5H12l-4.5 3.5V19H7.5A2.5 2.5 0 015 16.5v-8z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
      <path d="M9.5 11h9M9.5 14h6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}
