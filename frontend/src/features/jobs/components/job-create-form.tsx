"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { AIMark } from "@/components/ui/ai-mark";
import { Button, buttonClasses } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useToast } from "@/components/ui/toast";
import { ApiError } from "@/lib/api-client";
import { useCreateJob } from "../hooks/use-jobs";
import { CURRENCY_LABELS, jobCreateSchema, type JobCreateInput } from "../types";
import { SkillChips } from "./skill-chips";

const FIELD_CLASSES =
  "mt-1.5 w-full rounded-md border border-line bg-white px-3 py-2.5 text-sm text-ink transition-colors placeholder:text-ink/30 focus:border-ink/30 focus:outline-none focus:ring-2 focus:ring-accent/30";

/** "Python, SQL ,, REST" → ["Python", "SQL", "REST"] — mirrors how the form is submitted. */
function parseSkills(text: string | undefined): string[] {
  return (text ?? "")
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
}

function SectionHeading({ title, hint }: { title: string; hint?: string }) {
  return (
    <div>
      <h2 className="text-sm font-medium text-ink">{title}</h2>
      {hint && <p className="mt-1 text-xs leading-relaxed text-ink/50">{hint}</p>}
    </div>
  );
}

export function JobCreateForm({ onSuccess }: { onSuccess?: (jobId: string) => void }) {
  const createJob = useCreateJob();
  const toast = useToast();
  const [serverError, setServerError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<JobCreateInput>({ resolver: zodResolver(jobCreateSchema) });

  const requiredPreview = parseSkills(watch("required_skills_text"));
  const preferredPreview = parseSkills(watch("preferred_skills_text"));

  async function onSubmit(values: JobCreateInput) {
    setServerError(null);
    try {
      const job = await createJob.mutateAsync(values);
      toast.success("Job created");
      onSuccess?.(job.id);
    } catch (err) {
      setServerError(err instanceof ApiError ? err.message : "Something went wrong.");
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-8">
      <Card className="flex flex-col gap-5 p-6">
        <SectionHeading title="The role" />
        <Input
          label="Title"
          placeholder="Backend Engineer"
          error={errors.title?.message}
          {...register("title")}
        />

        <div>
          <label htmlFor="job-description" className="block text-sm font-medium text-ink">
            Description
          </label>
          <textarea
            id="job-description"
            rows={6}
            aria-invalid={Boolean(errors.description)}
            className={FIELD_CLASSES}
            {...register("description")}
          />
          {errors.description && (
            <p className="mt-1.5 text-sm text-red-600">{errors.description.message}</p>
          )}
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label htmlFor="job-type" className="block text-sm font-medium text-ink">
              Employment type
            </label>
            <select id="job-type" className={FIELD_CLASSES} {...register("employment_type")}>
              <option value="full_time">Full-time</option>
              <option value="part_time">Part-time</option>
              <option value="contract">Contract</option>
              <option value="internship">Internship</option>
            </select>
          </div>
          <Input label="Location" placeholder="Remote" {...register("location")} />
        </div>
      </Card>

      <Card className="flex flex-col gap-5 p-6">
        <SectionHeading
          title="Compensation"
          hint="Optional. Shown to candidates on the public job page."
        />
        <div className="grid gap-4 sm:grid-cols-3">
          <Input label="Min salary" type="number" {...register("salary_min")} />
          <Input
            label="Max salary"
            type="number"
            error={errors.salary_max?.message}
            {...register("salary_max")}
          />
          <div>
            <label htmlFor="job-currency" className="block text-sm font-medium text-ink">
              Currency
            </label>
            <select id="job-currency" className={FIELD_CLASSES} {...register("salary_currency")}>
              {Object.entries(CURRENCY_LABELS).map(([code, label]) => (
                <option key={code} value={code}>
                  {label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </Card>

      <Card className="flex flex-col gap-5 p-6">
        <div className="flex items-start gap-3 rounded-md bg-ink/[0.04] px-4 py-3.5">
          <AIMark className="mt-0.5 h-4 w-4 shrink-0 text-accent" />
          <div>
            <p className="text-sm font-medium text-ink">Scoring criteria</p>
            <p className="mt-1 text-xs leading-relaxed text-ink/55">
              These fields — not the description above — are what Resume Intelligence scores
              candidates against. The description is context only.
            </p>
          </div>
        </div>

        <div>
          <Input
            label="Required skills"
            placeholder="Python, SQL, REST APIs"
            helperText="Comma-separated."
            {...register("required_skills_text")}
          />
          <SkillChips skills={requiredPreview} className="mt-2.5" />
        </div>

        <div>
          <Input
            label="Preferred skills"
            placeholder="Docker, Kubernetes"
            helperText="Comma-separated. Optional."
            {...register("preferred_skills_text")}
          />
          <SkillChips skills={preferredPreview} className="mt-2.5" />
        </div>

        <div className="sm:w-48">
          <Input
            label="Minimum years of experience"
            type="number"
            helperText="Optional — leave blank to skip this dimension."
            {...register("min_years_experience")}
          />
        </div>
      </Card>

      {serverError && <p className="text-sm text-red-600">{serverError}</p>}

      <div className="flex items-center gap-3">
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Creating…" : "Create job (draft)"}
        </Button>
        <Link href="/jobs" className={buttonClasses("ghost", "md")}>
          Cancel
        </Link>
      </div>
    </form>
  );
}
