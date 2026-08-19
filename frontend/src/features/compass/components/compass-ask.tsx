"use client";

import { useState } from "react";
import { ApiError } from "@/lib/api-client";
import { compassApi, type CompassCitation } from "../api";

interface Exchange {
  question: string;
  answer: string;
  citations: CompassCitation[] | null;
  confidence: "high" | "medium" | "low" | null;
}

export function CompassAsk({ applicationId }: { applicationId?: string }) {
  const [question, setQuestion] = useState("");
  const [exchanges, setExchanges] = useState<Exchange[]>([]);
  const [isAsking, setIsAsking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleAsk(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim()) return;
    setError(null);
    setIsAsking(true);
    const asked = question;
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

  return (
    <div className="flex flex-col gap-3 rounded-lg border border-gray-200 p-4">
      <p className="text-sm font-medium text-gray-900">Ask Compass</p>

      {exchanges.length > 0 && (
        <div className="flex flex-col gap-4">
          {exchanges.map((ex, i) => (
            <div key={i} className="text-sm">
              <p className="font-medium text-gray-700">{ex.question}</p>
              <p className="mt-1 text-gray-600">{ex.answer}</p>

              {ex.citations && ex.citations.length > 0 && (
                <div className="mt-2 flex flex-col gap-1.5">
                  {ex.citations.map((c) => (
                    <div
                      key={c.chunk_id}
                      className="rounded-md border border-gray-100 bg-gray-50 px-2.5 py-1.5 text-xs text-gray-500"
                    >
                      <p className="font-medium text-gray-600">{c.document_title}</p>
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

      <form onSubmit={handleAsk} className="flex gap-2">
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder={applicationId ? "Ask about this candidate…" : "Ask about company policies…"}
          disabled={isAsking}
          className="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm"
        />
        <button
          type="submit"
          disabled={isAsking || !question.trim()}
          className="rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {isAsking ? "…" : "Ask"}
        </button>
      </form>

      {error && <p className="text-sm text-red-600">{error}</p>}
    </div>
  );
}
