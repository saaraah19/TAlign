"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { RegisterCandidateForm } from "@/features/auth";

export default function RegisterCandidatePage() {
  const router = useRouter();

  return (
    <main className="mx-auto flex min-h-screen max-w-sm flex-col justify-center gap-6 p-8">
      <div>
        <h1 className="text-xl font-semibold">Create your candidate account</h1>
        <p className="mt-1 text-sm text-gray-500">
          One account, apply to any company on Talign.
        </p>
      </div>

      <RegisterCandidateForm onSuccess={() => router.push("/dashboard")} />

      <p className="text-center text-sm text-gray-500">
        Already have an account?{" "}
        <Link href="/login" className="font-medium text-gray-900 underline">
          Sign in
        </Link>
      </p>
    </main>
  );
}
