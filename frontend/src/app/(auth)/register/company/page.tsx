"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { AuthSplitLayout } from "@/components/auth-split-layout";
import { RegisterCompanyForm } from "@/features/auth";

export default function RegisterCompanyPage() {
  const router = useRouter();

  return (
    <AuthSplitLayout eyebrow="You'll be the first admin — invite your team afterward.">
      <h1 className="text-2xl font-semibold tracking-tight text-ink">
        Create your company workspace
      </h1>
      <p className="mt-1.5 text-sm text-ink/50">Takes about a minute.</p>

      <div className="mt-8">
        <RegisterCompanyForm onSuccess={() => router.push("/dashboard")} />
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
