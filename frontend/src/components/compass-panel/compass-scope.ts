import { hasRecruitingRole, isPlainEmployee } from "@/lib/roles";

/**
 * What can Compass honestly answer from where the user is standing?
 *
 * This mirrors the backend rule in Compass._resolve_capability_for_role
 * — it decides what to *offer*, the backend still decides what is
 * *allowed*:
 *   - staff (admin / recruiter / hiring manager) on a candidate page
 *     → questions about that candidate's stored analysis;
 *     anywhere → company policy questions
 *   - employees → company policy questions
 *   - candidates → only about their own application, never policies
 * A user for whom this returns an empty list is not offered the panel
 * at all, rather than offered a box that can only say "I can't help".
 */
export type CompassScope =
  | { kind: "application"; applicationId: string; audience: "staff" | "candidate" }
  | { kind: "company" };

const UUID = "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}";
const STAFF_APPLICATION_PATH = new RegExp(`^/pipeline/(${UUID})/?$`, "i");
const CANDIDATE_APPLICATION_PATH = new RegExp(`^/applications/(${UUID})/?$`, "i");

export function availableCompassScopes(
  user: { roles: string[]; account_type: string },
  pathname: string,
): CompassScope[] {
  if (user.account_type === "candidate") {
    const id = CANDIDATE_APPLICATION_PATH.exec(pathname)?.[1];
    return id ? [{ kind: "application", applicationId: id, audience: "candidate" }] : [];
  }

  if (hasRecruitingRole(user.roles)) {
    const id = STAFF_APPLICATION_PATH.exec(pathname)?.[1];
    return id
      ? [{ kind: "application", applicationId: id, audience: "staff" }, { kind: "company" }]
      : [{ kind: "company" }];
  }

  if (isPlainEmployee(user.roles)) return [{ kind: "company" }];

  return [];
}

export function scopeLabel(scope: CompassScope): string {
  if (scope.kind === "company") return "Company policies";
  return scope.audience === "staff" ? "This candidate" : "My application";
}

export function scopeDescription(scope: CompassScope): string {
  if (scope.kind === "company") {
    return "Answers come from your company's documents, with the source passages cited.";
  }
  return scope.audience === "staff"
    ? "Answers use this candidate's stored resume analysis — nothing new is scored."
    : "Compass can tell you where your application stands in the process.";
}
