"use client";

import { useState } from "react";
import { ApiError } from "@/lib/api-client";
import { useCreateLeaveRequest } from "../hooks/use-leave-requests";
import { LEAVE_TYPE_LABELS, type LeaveType } from "../types";

const LEAVE_TYPES: LeaveType[] = ["vacation", "sick", "personal"];

export function LeaveRequestForm() {
  const createLeaveRequest = useCreateLeaveRequest();

  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [leaveType, setLeaveType] = useState<LeaveType>("vacation");
  const [reason, setReason] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccess(false);
    try {
      await createLeaveRequest.mutateAsync({
        start_date: startDate,
        end_date: endDate,
        leave_type: leaveType,
        reason: reason || undefined,
      });
      setSuccess(true);
      setStartDate("");
      setEndDate("");
      setReason("");
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setError("This date range overlaps a pending or approved leave request you already have.");
      } else if (err instanceof ApiError && err.status === 422) {
        setError(err.message || "The end date must not be before the start date.");
      } else {
        setError(err instanceof ApiError ? err.message : "Could not submit your request.");
      }
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <div className="flex flex-col gap-3 sm:flex-row">
        <label className="flex flex-1 flex-col gap-1 text-sm">
          <span className="font-medium text-gray-900">Start date</span>
          <input
            type="date"
            required
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm"
          />
        </label>
        <label className="flex flex-1 flex-col gap-1 text-sm">
          <span className="font-medium text-gray-900">End date</span>
          <input
            type="date"
            required
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm"
          />
        </label>
      </div>

      <label className="flex flex-col gap-1 text-sm">
        <span className="font-medium text-gray-900">Type</span>
        <select
          value={leaveType}
          onChange={(e) => setLeaveType(e.target.value as LeaveType)}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm"
        >
          {LEAVE_TYPES.map((type) => (
            <option key={type} value={type}>
              {LEAVE_TYPE_LABELS[type]}
            </option>
          ))}
        </select>
      </label>

      <label className="flex flex-col gap-1 text-sm">
        <span className="font-medium text-gray-900">Reason (optional)</span>
        <textarea
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          rows={3}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm"
        />
      </label>

      {error && <p className="text-sm text-red-600">{error}</p>}
      {success && <p className="text-sm text-green-700">Request submitted.</p>}

      <button
        type="submit"
        disabled={createLeaveRequest.isPending}
        className="rounded-md bg-gray-900 px-5 py-2.5 text-sm font-medium text-white disabled:opacity-50"
      >
        {createLeaveRequest.isPending ? "Submitting…" : "Submit request"}
      </button>
    </form>
  );
}
