"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ApiError } from "@/lib/api-client";
import { useAuth } from "../hooks/use-auth";
import { registerCandidateSchema, type RegisterCandidateInput } from "../types";

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
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-5">
      <div className="grid grid-cols-2 gap-4">
        <Input label="First name" error={errors.first_name?.message} {...register("first_name")} />
        <Input label="Last name" error={errors.last_name?.message} {...register("last_name")} />
      </div>
      <Input label="Email" type="email" error={errors.email?.message} {...register("email")} />
      <Input
        label="Password"
        type="password"
        helperText="At least 8 characters."
        error={errors.password?.message}
        {...register("password")}
      />

      {serverError && (
        <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-600">{serverError}</p>
      )}

      <Button type="submit" disabled={isSubmitting} className="w-full">
        {isSubmitting ? "Creating your account…" : "Create candidate account"}
      </Button>
    </form>
  );
}
