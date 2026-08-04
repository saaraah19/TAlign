"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { ApiError } from "@/lib/api-client";
import { useCreateJob } from "../hooks/use-jobs";
import { CURRENCY_LABELS, jobCreateSchema, type JobCreateInput } from "../types";

export function JobCreateForm({ onSuccess }: { onSuccess?: (jobId: string) => void }) {
  const createJob = useCreateJob();
  const [serverError, setServerError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<JobCreateInput>({ resolver: zodResolver(jobCreateSchema) });

  async function onSubmit(values: JobCreateInput) {
    setServerError(null);
    try {
      const job = await createJob.mutateAsync(values);
      onSuccess?.(job.id);
    } catch (err) {
      setServerError(err instanceof ApiError ? err.message : "Something went wrong.");
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
      <div>
        <label className="block text-sm font-medium">Title</label>
        <input
          className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
          placeholder="Backend Engineer"
          {...register("title")}
        />
        {errors.title && <p className="mt-1 text-sm text-red-600">{errors.title.message}</p>}
      </div>

      <div>
        <label className="block text-sm font-medium">Description</label>
        <textarea
          rows={5}
          className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
          {...register("description")}
        />
        {errors.description && (
          <p className="mt-1 text-sm text-red-600">{errors.description.message}</p>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium">Employment type</label>
          <select
            className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            {...register("employment_type")}
          >
            <option value="full_time">Full-time</option>
            <option value="part_time">Part-time</option>
            <option value="contract">Contract</option>
            <option value="internship">Internship</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium">Location</label>
          <input
            className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            placeholder="Remote"
            {...register("location")}
          />
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div>
          <label className="block text-sm font-medium">Min salary</label>
          <input
            type="number"
            className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            {...register("salary_min")}
          />
        </div>
        <div>
          <label className="block text-sm font-medium">Max salary</label>
          <input
            type="number"
            className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            {...register("salary_max")}
          />
          {errors.salary_max && (
            <p className="mt-1 text-sm text-red-600">{errors.salary_max.message}</p>
          )}
        </div>
        <div>
          <label className="block text-sm font-medium">Currency</label>
          <select
            className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            {...register("salary_currency")}
          >
            {Object.entries(CURRENCY_LABELS).map(([code, label]) => (
              <option key={code} value={code}>
                {label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="border-t border-gray-200 pt-4">
        <p className="text-sm font-medium text-gray-900">Scoring criteria</p>
        <p className="mt-1 text-xs text-gray-500">
          These fields — not the description above — are what Resume Intelligence
          scores candidates against. The description is context only.
        </p>

        <div className="mt-3">
          <label className="block text-sm font-medium">Required skills</label>
          <input
            className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            placeholder="Python, SQL, REST APIs"
            {...register("required_skills_text")}
          />
          <p className="mt-1 text-xs text-gray-400">Comma-separated.</p>
        </div>

        <div className="mt-3">
          <label className="block text-sm font-medium">Preferred skills</label>
          <input
            className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            placeholder="Docker, Kubernetes"
            {...register("preferred_skills_text")}
          />
          <p className="mt-1 text-xs text-gray-400">Comma-separated. Optional.</p>
        </div>

        <div className="mt-3">
          <label className="block text-sm font-medium">Minimum years of experience</label>
          <input
            type="number"
            className="mt-1 w-32 rounded-md border border-gray-300 px-3 py-2 text-sm"
            {...register("min_years_experience")}
          />
          <p className="mt-1 text-xs text-gray-400">
            Optional — leave blank to skip this dimension.
          </p>
        </div>
      </div>

      {serverError && <p className="text-sm text-red-600">{serverError}</p>}

      <button
        type="submit"
        disabled={isSubmitting}
        className="rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
      >
        {isSubmitting ? "Creating…" : "Create job (draft)"}
      </button>
    </form>
  );
}
