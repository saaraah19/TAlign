"use client";

import { forwardRef, type InputHTMLAttributes, useId, useState } from "react";

/**
 * Talign design system — Input.
 *
 * One component handles label, helper text, error state, and a
 * show/hide toggle for password fields — every text field in the app
 * so far only ever needs this combination, so one component covers it
 * rather than a form-field wrapper plus a bare <input> repeated in
 * every form (the previous pattern — see the old register-company-form.tsx).
 */
interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
  helperText?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, helperText, id, type, className = "", ...props }, ref) => {
    const generatedId = useId();
    const inputId = id ?? generatedId;
    const [showPassword, setShowPassword] = useState(false);
    const isPassword = type === "password";

    return (
      <div>
        <label htmlFor={inputId} className="block text-sm font-medium text-ink">
          {label}
        </label>
        <div className="relative mt-1.5">
          <input
            ref={ref}
            id={inputId}
            type={isPassword && showPassword ? "text" : type}
            aria-invalid={Boolean(error)}
            className={`w-full rounded-md border px-3 py-2.5 text-sm text-ink transition-colors placeholder:text-ink/30 focus:outline-none focus:ring-2 focus:ring-accent/30 ${
              error ? "border-red-300 focus:border-red-400" : "border-line focus:border-ink/30"
            } ${isPassword ? "pr-16" : ""} ${className}`}
            {...props}
          />
          {isPassword && (
            <button
              type="button"
              onClick={() => setShowPassword((v) => !v)}
              tabIndex={-1}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-xs font-medium text-ink/40 hover:text-ink/70"
            >
              {showPassword ? "Hide" : "Show"}
            </button>
          )}
        </div>
        {error ? (
          <p className="mt-1.5 text-xs text-red-600">{error}</p>
        ) : helperText ? (
          <p className="mt-1.5 text-xs text-ink/40">{helperText}</p>
        ) : null}
      </div>
    );
  }
);
Input.displayName = "Input";
