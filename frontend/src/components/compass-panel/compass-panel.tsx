"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { AIMark } from "@/components/ui/ai-mark";
import { Skeleton } from "@/components/ui/skeleton";
import {
  ANALYSIS_SUGGESTIONS,
  CANDIDATE_APPLICATION_SUGGESTIONS,
  CompassAsk,
  policySuggestions,
} from "@/features/compass";
import { useKnowledgeDocuments } from "@/features/knowledge";
import { scopeDescription, scopeLabel, type CompassScope } from "./compass-scope";

/**
 * The global Compass panel. A native <dialog> opened with showModal():
 * the browser itself provides the focus trap, the Esc key, the dimmed
 * backdrop, and hides the page from screen readers behind it — all
 * things a hand-rolled overlay has to re-implement and usually gets
 * slightly wrong.
 *
 * The body only mounts while open, so closing the panel starts the next
 * conversation fresh and nothing (like the document lookup below) runs
 * while it is closed.
 */
export function CompassPanel({
  isOpen,
  onClose,
  scopes,
}: {
  isOpen: boolean;
  onClose: () => void;
  scopes: CompassScope[];
}) {
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (isOpen && !dialog.open) {
      dialog.showModal();
      // showModal() focuses the first focusable element, which is the
      // close button. A person opening Compass wants the question box.
      // React's autoFocus can't do this on first open: it runs while
      // the dialog is still closed, where nothing can take focus. (It
      // does still cover the box mounting later, after documents load.)
      dialog.querySelector<HTMLInputElement>("input")?.focus();
    }
    if (!isOpen && dialog.open) dialog.close();
  }, [isOpen]);

  // showModal() doesn't stop the page behind from scrolling.
  useEffect(() => {
    if (!isOpen) return;
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previous;
    };
  }, [isOpen]);

  return (
    <dialog
      ref={dialogRef}
      aria-label="Ask Compass"
      onClose={onClose}
      // A click on the dimmed area lands on the <dialog> element itself;
      // a click on anything inside lands on a child.
      onClick={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
      className="m-0 mx-auto mb-auto mt-[10vh] w-[min(40rem,calc(100vw-2rem))] max-w-none overflow-hidden rounded-xl border border-line bg-paper p-0 text-ink shadow-2xl backdrop:bg-ink/40 backdrop:backdrop-blur-sm open:animate-panel-in motion-reduce:animate-none"
    >
      {isOpen && <PanelBody scopes={scopes} onClose={onClose} />}
    </dialog>
  );
}

function PanelBody({ scopes, onClose }: { scopes: CompassScope[]; onClose: () => void }) {
  const [scopeIndex, setScopeIndex] = useState(0);
  const scope = scopes[Math.min(scopeIndex, scopes.length - 1)];
  if (!scope) return null;

  return (
    <div className="flex max-h-[75vh] flex-col">
      <div className="flex items-center justify-between border-b border-line px-5 py-3">
        <div className="flex items-center gap-2">
          <AIMark className="h-4 w-4 text-accent" />
          <h2 className="text-sm font-medium text-ink">Ask Compass</h2>
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close"
          className="flex items-center gap-2 text-xs text-ink/40 transition-colors hover:text-ink"
        >
          <kbd className="rounded border border-line px-1.5 py-0.5 text-[10px]">Esc</kbd>
        </button>
      </div>

      <div className="overflow-y-auto px-5 py-4">
        {scopes.length > 1 && (
          <div className="mb-3 flex gap-2" role="group" aria-label="What to ask about">
            {scopes.map((s, i) => {
              const active = i === scopeIndex;
              return (
                <button
                  key={s.kind}
                  type="button"
                  onClick={() => setScopeIndex(i)}
                  aria-pressed={active}
                  className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                    active ? "bg-ink text-white" : "bg-ink/[0.05] text-ink/65 hover:bg-ink/[0.09]"
                  }`}
                >
                  {scopeLabel(s)}
                </button>
              );
            })}
          </div>
        )}
        <p className="mb-4 text-xs text-ink/45">{scopeDescription(scope)}</p>

        {scope.kind === "application" ? (
          <CompassAsk
            key={scope.applicationId}
            applicationId={scope.applicationId}
            suggestions={
              scope.audience === "staff" ? ANALYSIS_SUGGESTIONS : CANDIDATE_APPLICATION_SUGGESTIONS
            }
            showHeader={false}
            autoFocus
            bare
          />
        ) : (
          <CompanyScopeBody onClose={onClose} />
        )}
      </div>
    </div>
  );
}

/**
 * Company questions are answered from uploaded documents, so with none
 * ready there is nothing to ask — say so and point at where to fix it,
 * instead of showing an input that can only disappoint.
 */
function CompanyScopeBody({ onClose }: { onClose: () => void }) {
  const { data, isLoading } = useKnowledgeDocuments({ pageSize: 100 });

  if (isLoading) return <Skeleton className="h-24 w-full" />;

  const readyTitles = (data?.items ?? []).filter((d) => d.status === "ready").map((d) => d.title);

  // A failed lookup (data undefined) still shows the box: asking can
  // work even if the suggestion list could not load.
  if (data && readyTitles.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-line px-5 py-8 text-center">
        <p className="text-sm font-medium text-ink">Compass has no documents to answer from yet</p>
        <p className="mx-auto mt-1.5 max-w-sm text-xs leading-relaxed text-ink/50">
          Answers appear here once documents have been uploaded and processed in the Knowledge
          Center.
        </p>
        <Link
          href="/knowledge"
          onClick={onClose}
          className="mt-4 inline-block text-xs font-medium text-ink underline underline-offset-2"
        >
          Open the Knowledge Center
        </Link>
      </div>
    );
  }

  return (
    <CompassAsk suggestions={policySuggestions(readyTitles)} showHeader={false} autoFocus bare />
  );
}
