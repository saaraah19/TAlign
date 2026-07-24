"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api-client";

interface HealthResponse {
  status: string;
  database: string;
}

export default function HomePage() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<HealthResponse>("/health")
      .then(setHealth)
      .catch((e) => setError(e instanceof Error ? e.message : "Unknown error"));
  }, []);

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6 p-8">
      <div className="text-center">
        <h1 className="text-2xl font-semibold">Talign</h1>
        <p className="text-sm text-gray-500">Slice 4 — Resume Intelligence</p>
      </div>

      <div className="rounded-lg border border-gray-200 px-4 py-3 text-sm">
        {health && (
          <p>
            Backend status: <span className="font-mono">{health.status}</span> · Database:{" "}
            <span className="font-mono">{health.database}</span>
          </p>
        )}
        {error && (
          <p className="text-red-600">
            Could not reach backend ({error}). Is the backend service running?
          </p>
        )}
      </div>

      <div className="flex gap-4 text-sm">
        <Link href="/login" className="rounded-md bg-gray-900 px-4 py-2 font-medium text-white">
          Sign in
        </Link>
        <Link
          href="/register/company"
          className="rounded-md border border-gray-300 px-4 py-2 font-medium"
        >
          Register a company
        </Link>
        <Link
          href="/register/candidate"
          className="rounded-md border border-gray-300 px-4 py-2 font-medium"
        >
          Register as candidate
        </Link>
      </div>
    </main>
  );
}