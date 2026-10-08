import { type ButtonHTMLAttributes, forwardRef } from "react";

/**
 * Talign design system — Button.
 *
 * Four variants cover every button in the app so far: `primary` (the
 * one high-intent action per screen), `secondary` (bordered, for the
 * second action next to a primary), `ghost` (text-only, for tertiary
 * actions inside dense UI like table rows), `danger` (destructive
 * actions — reject, delete, cancel). Never introduce a fifth variant
 * without a real recurring need — see CLAUDE.md's "avoid unnecessary
 * abstractions."
 */
type Variant = "primary" | "secondary" | "ghost" | "danger";
type Size = "sm" | "md";

const VARIANT_CLASSES: Record<Variant, string> = {
  primary: "bg-ink text-white hover:bg-ink-700 disabled:bg-ink/40",
  secondary:
    "border border-line bg-white text-ink hover:border-ink/30 hover:bg-paper disabled:opacity-50",
  ghost: "text-ink/60 hover:bg-ink/[0.05] hover:text-ink disabled:opacity-40",
  danger: "border border-red-200 bg-white text-red-600 hover:bg-red-50 disabled:opacity-50",
};

const SIZE_CLASSES: Record<Size, string> = {
  sm: "px-3 py-1.5 text-xs",
  md: "px-4 py-2.5 text-sm",
};

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "primary", size = "md", className = "", ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={`inline-flex items-center justify-center gap-2 rounded-md font-medium transition-colors duration-150 disabled:cursor-not-allowed ${VARIANT_CLASSES[variant]} ${SIZE_CLASSES[size]} ${className}`}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";
