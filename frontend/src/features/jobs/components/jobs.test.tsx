import { fireEvent, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { apiMock } from "@/test/api-mock";
import { staffJob } from "@/test/fixtures";
import { admin, renderApp } from "@/test/render-app";
import { JobCreateForm } from "./job-create-form";
import { JobDetail } from "./job-detail";

const type = (label: string | RegExp, value: string) =>
  fireEvent.change(screen.getByLabelText(label), { target: { value } });

describe("JobCreateForm", () => {
  const setup = (onSuccess = vi.fn()) => {
    apiMock.on("POST", "/jobs", staffJob({ id: "job-new" }));
    renderApp(<JobCreateForm onSuccess={onSuccess} />, { user: admin() });
    return onSuccess;
  };

  it("previews the skills as chips while typing, dropping blank entries", () => {
    setup();

    type("Required skills", "Python, SQL ,, REST APIs");

    expect(screen.getAllByRole("listitem").map((li) => li.textContent)).toEqual(["Python", "SQL", "REST APIs"]);
  });

  it("previews preferred skills too", () => {
    setup();
    type("Required skills", "Python");
    type("Preferred skills", "Docker, Go");

    expect(screen.getAllByRole("listitem")).toHaveLength(3);
  });

  it("blocks an invalid title and marks the field", async () => {
    setup();
    type("Title", "A");
    type("Description", "Build APIs");

    fireEvent.click(screen.getByRole("button", { name: /Create job/ }));

    await waitFor(() => expect(screen.getByLabelText("Title")).toHaveAttribute("aria-invalid", "true"));
    expect(apiMock.writes).toHaveLength(0);
  });

  it("refuses a minimum salary above the maximum", async () => {
    setup();
    type("Title", "Backend Engineer");
    type("Description", "Build APIs");
    type("Min salary", "90000");
    type("Max salary", "80000");

    fireEvent.click(screen.getByRole("button", { name: /Create job/ }));

    expect(await screen.findByText(/Minimum salary cannot exceed maximum salary/)).toBeInTheDocument();
    expect(apiMock.writes).toHaveLength(0);
  });

  it("posts the skills as arrays, confirms with a toast, and reports the new id", async () => {
    const onSuccess = setup();
    type("Title", "Backend Engineer");
    type("Description", "Build APIs");
    type("Required skills", "Python, SQL ,, REST APIs");
    type("Preferred skills", "Docker");

    fireEvent.click(screen.getByRole("button", { name: /Create job/ }));

    await waitFor(() => expect(onSuccess).toHaveBeenCalledWith("job-new"));
    const body = apiMock.find("POST", "/jobs")?.body as Record<string, unknown>;
    expect(body.title).toBe("Backend Engineer");
    expect(body.required_skills).toEqual(["Python", "SQL", "REST APIs"]);
    expect(body.preferred_skills).toEqual(["Docker"]);
    expect(await screen.findByText("Job created")).toBeInTheDocument();
  });

  it("offers a way back without saving", () => {
    setup();

    expect(screen.getByRole("link", { name: "Cancel" })).toHaveAttribute("href", "/jobs");
  });
});

describe("JobDetail", () => {
  const setup = (job: Record<string, unknown>, onDeleted = vi.fn()) => {
    apiMock.on("GET", "/jobs/job-1", job);
    apiMock.on("POST", "/jobs/job-1/transition", job);
    apiMock.on("DELETE", "/jobs/job-1", { status: 204 });
    renderApp(<JobDetail jobId="job-1" onDeleted={onDeleted} />, { user: admin() });
    return onDeleted;
  };

  it("shows the scoring criteria the AI uses", async () => {
    setup(staffJob({ status: "draft" }));

    expect(await screen.findByText("Scoring criteria")).toBeInTheDocument();
    expect(screen.getByText("Python")).toBeInTheDocument();
    expect(screen.getByText("Kubernetes")).toBeInTheDocument();
    expect(screen.getByText("3 years")).toBeInTheDocument();
  });

  it("explains a job with no criteria instead of showing nothing", async () => {
    setup(staffJob({ status: "open", required_skills: [], preferred_skills: [], min_years_experience: null }));

    expect(await screen.findByText(/No required skills were set/)).toBeInTheDocument();
  });

  it("offers publish, delete and applicants for a draft", async () => {
    setup(staffJob({ status: "draft" }));

    expect(await screen.findByRole("button", { name: "Move to Open" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Delete draft" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "View applicants" })).toHaveAttribute("href", "/pipeline?job_id=job-1");
  });

  it("never offers deleting a job that is not a draft", async () => {
    setup(staffJob({ status: "open" }));

    expect(await screen.findByRole("button", { name: "Move to Closed" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Delete draft" })).not.toBeInTheDocument();
  });

  it("publishes through the transition endpoint and confirms", async () => {
    setup(staffJob({ status: "draft" }));

    fireEvent.click(await screen.findByRole("button", { name: "Move to Open" }));

    expect(await screen.findByText("Job is now open")).toBeInTheDocument();
    expect(apiMock.find("POST", "/jobs/job-1/transition")?.body).toEqual({ target_status: "open" });
  });

  it("asks before deleting, and deletes nothing until confirmed", async () => {
    const onDeleted = setup(staffJob({ status: "draft" }));
    fireEvent.click(await screen.findByRole("button", { name: "Delete draft" }));

    expect(screen.getByText(/can't be undone/)).toBeInTheDocument();
    expect(apiMock.writes).toHaveLength(0);

    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(screen.queryByText(/can't be undone/)).not.toBeInTheDocument();
    expect(apiMock.writes).toHaveLength(0);

    fireEvent.click(screen.getByRole("button", { name: "Delete draft" }));
    fireEvent.click(screen.getByRole("button", { name: "Confirm delete" }));

    await waitFor(() => expect(onDeleted).toHaveBeenCalled());
    expect(apiMock.find("DELETE", "/jobs/job-1")).toBeDefined();
    expect(await screen.findByText("Job deleted")).toBeInTheDocument();
  });
});
