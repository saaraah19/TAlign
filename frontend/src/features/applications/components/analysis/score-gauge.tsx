"use client";

import { useEffect, useState } from "react";
import {
  SCORE_BAND_LABELS,
  SCORE_BAND_STROKE,
  SCORE_BAND_TEXT,
  scoreBand,
} from "../../lib/score";

const RADIUS = 52;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

/**
 * The overall alignment score as a ring. The ring fills in after mount
 * (one frame later) so the stroke animates from empty instead of just
 * appearing — the only motion on this page, and it carries meaning:
 * it draws the eye to the number first.
 */
export function ScoreGauge({ score }: { score: number | null }) {
  const [filled, setFilled] = useState(false);
  useEffect(() => {
    const id = requestAnimationFrame(() => setFilled(true));
    return () => cancelAnimationFrame(id);
  }, []);

  if (score === null) {
    return (
      <div className="flex h-32 w-32 items-center justify-center rounded-full border border-dashed border-line text-sm text-ink/40">
        No score
      </div>
    );
  }

  const band = scoreBand(score);
  const clamped = Math.max(0, Math.min(100, score));
  const offset = CIRCUMFERENCE * (1 - (filled ? clamped : 0) / 100);

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative h-32 w-32">
        <svg viewBox="0 0 120 120" className="h-full w-full -rotate-90">
          <circle cx="60" cy="60" r={RADIUS} fill="none" strokeWidth="8" className="stroke-ink/[0.07]" />
          <circle
            cx="60"
            cy="60"
            r={RADIUS}
            fill="none"
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={CIRCUMFERENCE}
            strokeDashoffset={offset}
            className={`${SCORE_BAND_STROKE[band]} transition-[stroke-dashoffset] duration-700 ease-out`}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-3xl font-semibold tracking-tight text-ink">
            {Math.round(score)}
          </span>
          <span className="text-[11px] text-ink/40">out of 100</span>
        </div>
      </div>
      <span className={`text-xs font-medium ${SCORE_BAND_TEXT[band]}`}>
        {SCORE_BAND_LABELS[band]}
      </span>
    </div>
  );
}
