"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ApiError } from "@/lib/api-client";
import { useAuth } from "../hooks/use-auth";
import { registerCompanySchema, type RegisterCompanyInput } from "../types";

const STEPS = [
  { key: "company", label: "Company" },
  { key: "profile", label: "Your profile" },
] as const;

export function RegisterCompanyForm({ onSuccess }: { onSuccess?: () => void }) {
  const { registerCompany } = useAuth();
  const [step, setStep] = useState<0 | 1>(0);
  const [serverError, setServerError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    trigger,
    formState: { errors, isSubmitting },
  } = useForm<RegisterCompanyInput>({ resolver: zodResolver(registerCompanySchema) });

  async function goToProfileStep() {
    const valid = await trigger("company_name");
    if (valid) setStep(1);
  }

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
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-6">
      {/* Progress indicator */}
      <div className="flex items-center gap-3">
        {STEPS.map((s, i) => (
          <div key={s.key} className="flex items-center gap-3">
            <div className="flex items-center gap-1.5">
              <span
                className={`h-1.5 w-1.5 rounded-full ${
                  i <= step ? "bg-ink" : "bg-line"
                }`}
              />
              <span className={`text-xs font-medium ${i === step ? "text-ink" : "text-ink/35"}`}>
                {s.label}
              </span>
            </div>
            {i < STEPS.length - 1 && <span className="h-px w-6 bg-line" />}
          </div>
        ))}
      </div>

      {/* Step 1 — Company. Kept mounted (just hidden) rather than
          conditionally rendered, so react-hook-form's registration
          for company_name survives moving to step 2 and back. */}
      <div className={step === 0 ? "flex flex-col gap-5" : "hidden"}>
        <Input
          label="Company name"
          error={errors.company_name?.message}
          {...register("company_name")}
        />
        <Button type="button" onClick={goToProfileStep} className="w-full">
          Continue
        </Button>
      </div>

      {/* Step 2 — admin profile */}
      <div className={step === 1 ? "flex flex-col gap-5" : "hidden"}>
        <div className="grid grid-cols-2 gap-4">
          <Input
            label="First name"
            error={errors.admin_first_name?.message}
            {...register("admin_first_name")}
          />
          <Input
            label="Last name"
            error={errors.admin_last_name?.message}
            {...register("admin_last_name")}
          />
        </div>
        <Input
          label="Work email"
          type="email"
          error={errors.email?.message}
          {...register("email")}
        />
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

        <div className="flex gap-3">
          <Button type="button" variant="secondary" onClick={() => setStep(0)}>
            Back
          </Button>
          <Button type="submit" disabled={isSubmitting} className="flex-1">
            {isSubmitting ? "Creating your workspace…" : "Create company workspace"}
          </Button>
        </div>
      </div>
    </form>
  );
}
