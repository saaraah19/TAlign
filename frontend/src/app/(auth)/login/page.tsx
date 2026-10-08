"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { AuthSplitLayout } from "@/components/auth-split-layout";
import { LoginForm } from "@/features/auth";

export default function LoginPage() {
  const router = useRouter();

  return (
    <AuthSplitLayout eyebrow="Talign — AI-native Talent Operating System">
      <h1 className="text-2xl font-semibold tracking-tight text-ink">Welcome back</h1>
      <p className="mt-1.5 text-sm text-ink/50">Sign in to your workspace.</p>

      <div className="mt-8">
        <LoginForm onSuccess={() => router.push("/dashboard")} />
      </div>

      <p className="mt-8 text-center text-sm text-ink/50">
        New to Talign?{" "}
        <Link href="/register/company" className="font-medium text-ink underline underline-offset-2">
          Register your company
        </Link>{" "}
        or{" "}
        <Link href="/register/candidate" className="font-medium text-ink underline underline-offset-2">
          apply as a candidate
        </Link>
        .
      </p>
    </AuthSplitLayout>
  );
}
