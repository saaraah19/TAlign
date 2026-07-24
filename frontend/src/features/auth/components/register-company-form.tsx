"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { useAuth } from "../hooks/use-auth";
import { registerCompanySchema, type RegisterCompanyInput } from "../types";
import { ApiError } from "@/lib/api-client";

export function RegisterCompanyForm({ onSuccess }: { onSuccess?: () => void }) {
  const { registerCompany } = useAuth();
  const [serverError, setServerError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterCompanyInput>({ resolver: zodResolver(registerCompanySchema) });

  async function onSubmit(values: RegisterCompanyInput) {
    setServerError(null);
    try {
      await registerCompany(values);
      onSuccess?.();
    } catch (err) {
      setServerError(err instanceof ApiError ? err.message : "Something went wrong.");
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
      <Field label="Company name" error={errors.company_name?.message}>
        <input
          className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
          {...register("company_name")}
        />
      </Field>

      <div className="grid grid-cols-2 gap-4">
        <Field label="Your first name" error={errors.admin_first_name?.message}>
          <input
            className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            {...register("admin_first_name")}
          />
        </Field>
        <Field label="Your last name" error={errors.admin_last_name?.message}>
          <input
            className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            {...register("admin_last_name")}
          />
        </Field>
      </div>

      <Field label="Work email" error={errors.email?.message}>
        <input
          type="email"
          className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
          {...register("email")}
        />
      </Field>

      <Field label="Password" error={errors.password?.message}>
        <input
          type="password"
          className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
          {...register("password")}
        />
      </Field>

      {serverError && <p className="text-sm text-red-600">{serverError}</p>}

      <button
        type="submit"
        disabled={isSubmitting}
        className="rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
      >
        {isSubmitting ? "Creating your workspace…" : "Create company workspace"}
      </button>
    </form>
  );
}

function Field({
  label,
  error,
  children,
}: {
  label: string;
  error?: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label className="block text-sm font-medium">{label}</label>
      {children}
      {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
    </div>
  );
}
