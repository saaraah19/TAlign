"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { RegisterCompanyForm } from "@/features/auth";

export default function RegisterCompanyPage() {
  const router = useRouter();

  return (
    <main className="mx-auto flex min-h-screen max-w-sm flex-col justify-center gap-6 p-6 sm:p-8">
      <div>
        <h1 className="text-xl font-semibold">Set up your company</h1>
        <p className="mt-1 text-sm text-gray-500">
          You'll be the first admin — invite your team afterward.
        </p>
      </div>

      <RegisterCompanyForm onSuccess={() => router.push("/dashboard")} />

      <p className="text-center text-sm text-gray-500">
        Already have an account?{" "}
        <Link href="/login" className="font-medium text-gray-900 underline">
          Sign in
        </Link>
      </p>
    </main>
  );
}
