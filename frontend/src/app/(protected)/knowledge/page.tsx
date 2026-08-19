"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "@/features/auth";
import { CompassAsk } from "@/features/compass";
import { DocumentList, DocumentUpload } from "@/features/knowledge";

// Read access mirrors the backend's knowledge_query Compass capability
// scope (ADMIN/RECRUITER/HIRING_MANAGER) — see app/api/v1/knowledge.py's
// module docstring on the backend for why this list, not just ADMIN.
const READ_ROLES = ["admin", "recruiter", "hiring_manager"];

export default function KnowledgePage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !user) router.replace("/login");
  }, [isLoading, user, router]);

  if (isLoading || !user) return <main className="p-8 text-sm text-gray-500">Loading…</main>;

  const canRead = user.roles.some((role) => READ_ROLES.includes(role));
  const canManage = user.roles.includes("admin");

  if (!canRead) {
    return (
      <main className="mx-auto max-w-3xl p-8">
        <p className="text-sm text-gray-500">
          The Knowledge Center isn't available for your role yet.
        </p>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-3xl p-8">
      <h1 className="text-xl font-semibold">Knowledge Center</h1>
      <p className="mt-1 text-sm text-gray-500">
        Company policies, benefits, and procedures Compass can answer questions from.
      </p>

      {canManage && (
        <div className="mt-6">
          <DocumentUpload />
        </div>
      )}

      <div className="mt-6">
        <DocumentList canManage={canManage} />
      </div>

      <div className="mt-6">
        <CompassAsk />
      </div>
    </main>
  );
}
