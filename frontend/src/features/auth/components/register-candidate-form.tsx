"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { useAuth } from "../hooks/use-auth";
import { registerCandidateSchema, type RegisterCandidateInput } from "../types";
import { ApiError } from "@/lib/api-client";

export function RegisterCandidateForm({ onSuccess }: { onSuccess?: () => void }) {
  const { registerCandidate } = useAuth();
  const [serverError, setServerError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterCandidateInput>({ resolver: zodResolver(registerCandidateSchema) });

  async function onSubmit(values: RegisterCandidateInput) {
    setServerError(null);
    try {
      await registerCandidate(values);
      onSuccess?.();
    } catch (err) {
      setServerError(err instanceof ApiError ? err.message : "Something went wrong.");
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium">First name</label>
          <input
            className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            {...register("first_name")}
          />
          {errors.first_name && (
            <p className="mt-1 text-sm text-red-600">{errors.first_name.message}</p>
          )}
        </div>
        <div>
          <label className="block text-sm font-medium">Last name</label>
          <input
            className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            {...register("last_name")}
          />
          {errors.last_name && (
            <p className="mt-1 text-sm text-red-600">{errors.last_name.message}</p>
          )}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium">Email</label>
        <input
          type="email"
          className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
          {...register("email")}
        />
        {errors.email && <p className="mt-1 text-sm text-red-600">{errors.email.message}</p>}
      </div>

      <div>
        <label className="block text-sm font-medium">Password</label>
        <input
          type="password"
          className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
          {...register("password")}
        />
        {errors.password && (
          <p className="mt-1 text-sm text-red-600">{errors.password.message}</p>
        )}
      </div>

      {serverError && <p className="text-sm text-red-600">{serverError}</p>}

      <button
        type="submit"
        disabled={isSubmitting}
        className="rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
      >
        {isSubmitting ? "Creating your account…" : "Create candidate account"}
      </button>
    </form>
  );
}
