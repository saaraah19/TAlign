/**
 * Shared role groupings for frontend routing/UI decisions.
 *
 * UX-only, same as middleware.ts — the backend's require_roles() is the
 * real security boundary. These just decide what to *show*.
 *
 * `account_type === "internal"` is NOT enough to mean "recruiter side":
 * a hired employee is also internal (see AuthService.
 * convert_candidate_to_employee), so anything recruiter-only must check
 * roles, not account_type.
 */
export const RECRUITING_ROLES = ["admin", "recruiter", "hiring_manager"];

export function hasRecruitingRole(roles: string[]): boolean {
  return roles.some((role) => RECRUITING_ROLES.includes(role));
}

export function isPlainEmployee(roles: string[]): boolean {
  return !hasRecruitingRole(roles) && roles.includes("employee");
}
