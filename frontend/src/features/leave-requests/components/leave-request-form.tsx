"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useToast } from "@/components/ui/toast";
import { ApiError } from "@/lib/api-client";
import { useCreateLeaveRequest, useMyLeaveBalance } from "../hooks/use-leave-requests";
import { leaveDayCount } from "../lib/format-date-range";
import { LEAVE_TYPE_LABELS, type LeaveType } from "../types";

const LEAVE_TYPES: LeaveType[] = ["vacation", "sick", "personal"];

const FIELD_CLASSES =
  "mt-1.5 w-full rounded-md border border-line bg-white px-3 py-2.5 text-sm text-ink transition-colors placeholder:text-ink/30 focus:border-ink/30 focus:outline-none focus:ring-2 focus:ring-accent/30";

export function LeaveRequestForm() {
  const createLeaveRequest = useCreateLeaveRequest();
  const { data: balance } = useMyLeaveBalance();
  const toast = useToast();

  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [leaveType, setLeaveType] = useState<LeaveType>("vacation");
  const [reason, setReason] = useState("");
  const [error, setError] = useState<string | null>(null);

  // A live preview of what the request would use. It is the same
  // inclusive calendar-day count the backend applies to the balance, so
  // the number here can't disagree with the one that gets deducted.
  const days =
    startDate && endDate && endDate >= startDate ? leaveDayCount(startDate, endDate) : null;
  const remainingAfter = days !== null && balance ? balance.days_remaining - days : null;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await createLeaveRequest.mutateAsync({
        start_date: startDate,
        end_date: endDate,
        leave_type: leaveType,
        reason: reason || undefined,
      });
      toast.success("Request submitted — it's now waiting for review");
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
    <Card className="p-6">
      <form onSubmit={handleSubmit} className="flex flex-col gap-5">
        <div className="grid gap-4 sm:grid-cols-2">
          <Input
            label="Start date"
            type="date"
            required
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
          />
          <Input
            label="End date"
            type="date"
            required
            min={startDate || undefined}
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
          />
        </div>

        {days !== null && (
          <p className="rounded-md bg-ink/[0.04] px-3.5 py-2.5 text-sm text-ink/70">
            <span className="font-medium text-ink">
              {days} {days === 1 ? "day" : "days"}
            </span>
            {remainingAfter !== null &&
              (remainingAfter >= 0 ? (
                <> · if approved, you&apos;d have {remainingAfter} left this year</>
              ) : (
                <span className="text-amber-700">
                  {" "}
                  · this goes {Math.abs(remainingAfter)} beyond your balance; an admin can still
                  approve it
                </span>
              ))}
          </p>
        )}

        <div>
          <label htmlFor="leave-type" className="block text-sm font-medium text-ink">
            Type
          </label>
          <select
            id="leave-type"
            value={leaveType}
            onChange={(e) => setLeaveType(e.target.value as LeaveType)}
            className={FIELD_CLASSES}
          >
            {LEAVE_TYPES.map((type) => (
              <option key={type} value={type}>
                {LEAVE_TYPE_LABELS[type]}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="leave-reason" className="block text-sm font-medium text-ink">
            Reason <span className="font-normal text-ink/40">(optional)</span>
          </label>
          <textarea
            id="leave-reason"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            rows={3}
            className={FIELD_CLASSES}
          />
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <Button type="submit" disabled={createLeaveRequest.isPending}>
          {createLeaveRequest.isPending ? "Submitting…" : "Submit request"}
        </Button>
      </form>
    </Card>
  );
}
