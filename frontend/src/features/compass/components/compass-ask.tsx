"use client";

import { useState } from "react";
import { AIMark } from "@/components/ui/ai-mark";
import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api-client";
import { compassApi, type CompassCitation } from "../api";

interface Exchange {
  question: string;
  answer: string;
  citations: CompassCitation[] | null;
  confidence: "high" | "medium" | "low" | null;
}

/**
 * `suggestions` are optional starter questions shown while the
 * conversation is empty. They are fixed text chosen by the page that
 * renders this component (e.g. "What are this candidate's biggest
 * gaps?") — never generated data — and clicking one asks it exactly as
 * if it had been typed.
 */
export function CompassAsk({
  applicationId,
  suggestions,
  showHeader = true,
  autoFocus = false,
  bare = false,
}: {
  applicationId?: string;
  suggestions?: string[];
  /** Turn off the built-in "Ask Compass" title when a parent already supplies a heading. */
  showHeader?: boolean;
  /** Focus the question box on mount (used when Compass opens in the command panel). */
  autoFocus?: boolean;
  /** Drop the card border/padding when a parent already provides the surface. */
  bare?: boolean;
}) {
  const [question, setQuestion] = useState("");
  const [exchanges, setExchanges] = useState<Exchange[]>([]);
  const [isAsking, setIsAsking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function ask(asked: string) {
    if (!asked.trim() || isAsking) return;
    setError(null);
    setIsAsking(true);
    setQuestion("");
    try {
      const response = await compassApi.ask(asked, applicationId);
      setExchanges((prev) => [
        ...prev,
        {
          question: asked,
          answer: response.message,
          citations: response.citations,
          confidence: response.confidence,
        },
      ]);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Compass couldn't answer that.");
    } finally {
      setIsAsking(false);
    }
  }

  function handleAsk(e: React.FormEvent) {
    e.preventDefault();
    void ask(question);
  }

  return (
    <div
      className={`flex flex-col gap-3 ${bare ? "" : "rounded-lg border border-line bg-white p-5"}`}
    >
      {showHeader && (
        <div className="flex items-center gap-2">
          <AIMark className="h-4 w-4 text-accent" />
          <p className="text-sm font-medium text-ink">Ask Compass</p>
        </div>
      )}

      {exchanges.length === 0 && suggestions && suggestions.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {suggestions.map((s) => (
            <button
              key={s}
              onClick={() => void ask(s)}
              disabled={isAsking}
              className="rounded-full border border-line px-3 py-1 text-xs text-ink/65 transition-colors hover:border-ink/30 hover:text-ink disabled:opacity-50"
            >
              {s}
            </button>
          ))}
        </div>
      )}

      {exchanges.length > 0 && (
        <div className="flex flex-col gap-4">
          {exchanges.map((ex, i) => (
            <div key={i} className="text-sm">
              <p className="font-medium text-ink">{ex.question}</p>
              <p className="mt-1 leading-relaxed text-ink/70">{ex.answer}</p>

              {ex.citations && ex.citations.length > 0 && (
                <div className="mt-2 flex flex-col gap-1.5">
                  {ex.citations.map((c) => (
                    <div
                      key={c.chunk_id}
                      className="rounded-md border border-line bg-paper px-2.5 py-1.5 text-xs text-ink/55"
                    >
                      <p className="font-medium text-ink/70">{c.document_title}</p>
                      <p className="mt-0.5 italic">&ldquo;{c.excerpt}&rdquo;</p>
                    </div>
                  ))}
                </div>
              )}

              {ex.confidence && ex.confidence !== "high" && (
                <p className="mt-1 text-xs text-amber-600">
                  {ex.confidence === "medium" ? "Moderate" : "Low"} confidence — worth double
                  checking with HR.
                </p>
              )}
            </div>
          ))}
        </div>
      )}

      {isAsking && (
        <div className="flex items-center gap-2 text-xs text-ink/50">
          <span className="h-3 w-3 animate-spin rounded-full border-2 border-line border-t-ink" />
          Compass is thinking…
        </div>
      )}

      <form onSubmit={handleAsk} className="flex gap-2">
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder={applicationId ? "Ask about this candidate…" : "Ask about company policies…"}
          disabled={isAsking}
          autoFocus={autoFocus}
          className="min-w-0 flex-1 rounded-md border border-line bg-white px-3 py-2 text-sm text-ink outline-none transition-colors placeholder:text-ink/35 focus:border-ink/40 disabled:bg-paper"
        />
        <Button type="submit" disabled={isAsking || !question.trim()}>
          Ask
        </Button>
      </form>

      {error && <p className="text-sm text-red-600">{error}</p>}
    </div>
  );
}
