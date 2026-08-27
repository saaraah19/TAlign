"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { LoginForm } from "@/features/auth";

export default function LoginPage() {
  const router = useRouter();

  return (
    <main className="mx-auto flex min-h-screen max-w-sm flex-col justify-center gap-6 p-6 sm:p-8">
      <div>
        <h1 className="text-xl font-semibold">Sign in to Talign</h1>
        <p className="mt-1 text-sm text-gray-500">Welcome back.</p>
      </div>

      <LoginForm onSuccess={() => router.push("/dashboard")} />

      <p className="text-center text-sm text-gray-500">
        New to Talign?{" "}
        <Link href="/register/company" className="font-medium text-gray-900 underline">
          Register your company
        </Link>{" "}
        or{" "}
        <Link href="/register/candidate" className="font-medium text-gray-900 underline">
          apply as a candidate
        </Link>
        .
      </p>
    </main>
  );
}
