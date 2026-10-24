"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { AuthSplitLayout } from "@/components/auth-split-layout";
import { RegisterCandidateForm } from "@/features/auth";

export default function RegisterCandidatePage() {
  const router = useRouter();

  return (
    <AuthSplitLayout eyebrow="Track every application and get scored, transparent feedback.">
      <h1 className="text-2xl font-semibold tracking-tight text-ink">Create your account</h1>
      <p className="mt-1.5 text-sm text-ink/50">Apply to jobs and track your progress.</p>

      <div className="mt-8">
        <RegisterCandidateForm onSuccess={() => router.push("/dashboard")} />
      </div>

      <p className="mt-8 text-center text-sm text-ink/50">
        Already have an account?{" "}
        <Link href="/login" className="font-medium text-ink underline underline-offset-2">
          Sign in
        </Link>
      </p>
    </AuthSplitLayout>
  );
}
