"use client";

import { useState } from "react";
import { ApiError } from "@/lib/api-client";
import { compassApi } from "../api";

interface Exchange {
  question: string;
  answer: string;
}

export function CompassAsk({ applicationId }: { applicationId: string }) {
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
      const response = await compassApi.ask(applicationId, asked);
      setExchanges((prev) => [...prev, { question: asked, answer: response.message }]);
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
        <div className="flex flex-col gap-3">
          {exchanges.map((ex, i) => (
            <div key={i} className="text-sm">
              <p className="font-medium text-gray-700">{ex.question}</p>
              <p className="mt-1 text-gray-600">{ex.answer}</p>
            </div>
          ))}
        </div>
      )}

      <form onSubmit={handleAsk} className="flex gap-2">
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask a question…"
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
