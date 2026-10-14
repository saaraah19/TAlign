/** Shared sample payloads, shaped like the real API responses. */

export function publicJob(overrides: Record<string, unknown> = {}) {
  return {
    id: "job-1",
    company_name: "Acme Robotics",
    title: "Backend Engineer",
    description: "Build APIs.\nRun them.",
    employment_type: "full_time",
    location: "Remote",
    salary_min: 60000,
    salary_max: 80000,
    salary_currency: "USD",
    required_skills: ["Python", "SQL", "Docker", "AWS", "Redis", "Go"],
    preferred_skills: ["Kubernetes"],
    min_years_experience: 3,
    created_at: new Date().toISOString(),
    ...overrides,
  };
}

/** The staff-side view of a job (JobRead). */
export function staffJob(overrides: Record<string, unknown> = {}) {
  return {
    ...publicJob(),
    company_id: "company-1",
    created_by: "user-1",
    status: "open",
    updated_at: new Date().toISOString(),
    ...overrides,
  };
}

export function page<T>(items: T[], total = items.length, pageNumber = 1, pageSize = 20) {
  return { items, total, page: pageNumber, page_size: pageSize };
}

export function resume(id: string, name: string, status = "text_ready") {
  return {
    id,
    candidate_id: "user-1",
    original_filename: name,
    content_type: "application/pdf",
    file_size_bytes: 2048,
    status,
    parse_error: null,
    created_at: new Date().toISOString(),
  };
}
