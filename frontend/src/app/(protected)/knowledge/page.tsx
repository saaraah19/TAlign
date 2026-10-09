"use client";

import { useAuth } from "@/features/auth";
import { KnowledgeCenter } from "@/features/knowledge";

// Read access mirrors the backend's knowledge_query Compass capability
// scope (ADMIN/RECRUITER/HIRING_MANAGER/EMPLOYEE) — see
// app/api/v1/knowledge.py's module docstring on the backend.
const READ_ROLES = ["admin", "recruiter", "hiring_manager", "employee"];

export default function KnowledgePage() {
  const { user } = useAuth();
  if (!user) return null; // guaranteed non-null by (protected)/layout.tsx

  const canRead = user.roles.some((role) => READ_ROLES.includes(role));
  const canManage = user.roles.includes("admin");

  if (!canRead) {
    return (
      <main className="mx-auto max-w-4xl px-6 py-8 sm:px-8">
        <p className="text-sm text-ink/50">
          The Knowledge Center isn&apos;t available for your role yet.
        </p>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-4xl px-6 py-8 sm:px-8">
      <h1 className="text-2xl font-semibold tracking-tight text-ink">Knowledge Center</h1>
      <p className="mt-1 text-sm text-ink/55">
        Company policies, benefits, and procedures Compass can answer questions from.
      </p>

      <div className="mt-8">
        <KnowledgeCenter canManage={canManage} />
      </div>
    </main>
  );
}
