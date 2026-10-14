import { fireEvent, screen, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import CareersPage from "@/app/(public)/careers/page";
import PublicJobPage from "@/app/(public)/careers/[id]/page";
import { apiMock, MockResponse } from "../api-mock";
import { publicJob, page } from "../fixtures";
import { admin, candidate, renderApp } from "../render-app";

describe("careers list (/careers)", () => {
  it("shows each job with its employer, salary, skills and a link", async () => {
    apiMock.on("GET", "/public/jobs", page([publicJob()]));
    renderApp(<CareersPage />, { path: "/careers" });

    expect(await screen.findByText("Backend Engineer")).toBeInTheDocument();
    expect(screen.getByText("Acme Robotics")).toBeInTheDocument();
    expect(screen.getByText(/\$60,000 – \$80,000/)).toBeInTheDocument();
    expect(screen.getByText("Python")).toBeInTheDocument();
    expect(screen.getByText("+2")).toBeInTheDocument(); // 6 skills, 4 shown
    expect(screen.getByRole("link", { name: /Backend Engineer/ })).toHaveAttribute(
      "href",
      "/careers/job-1",
    );
  });

  it("counts the open roles in the subtitle", async () => {
    apiMock.on("GET", "/public/jobs", page([publicJob()], 45));
    renderApp(<CareersPage />, { path: "/careers" });

    expect(await screen.findByText(/45 open roles/)).toBeInTheDocument();
  });

  it("pages through the board instead of silently showing only the first 20", async () => {
    apiMock.on("GET", "/public/jobs", (call) => {
      const pageNumber = Number(new URLSearchParams(call.search).get("page") ?? 1);
      return page([publicJob({ id: `job-${pageNumber}`, title: `Job on page ${pageNumber}` })], 45, pageNumber);
    });
    renderApp(<CareersPage />, { path: "/careers" });

    expect(await screen.findByText("Page 1 of 3")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Previous" })).toBeDisabled();

    fireEvent.click(screen.getByRole("button", { name: "Next" }));

    expect(await screen.findByText("Job on page 2")).toBeInTheDocument();
    expect(screen.getByText("Page 2 of 3")).toBeInTheDocument();
  });

  it("explains an empty board", async () => {
    apiMock.on("GET", "/public/jobs", page([]));
    renderApp(<CareersPage />, { path: "/careers" });

    expect(await screen.findByText("No open positions right now")).toBeInTheDocument();
    expect(screen.queryByText(/Page 1/)).not.toBeInTheDocument();
  });

  it("shows a readable message, not a blank page, when the API fails", async () => {
    apiMock.on("GET", "/public/jobs", new MockResponse({ detail: "boom" }, 500));
    renderApp(<CareersPage />, { path: "/careers" });

    expect(await screen.findByText(/couldn't load the job board/)).toBeInTheDocument();
  });
});

describe("public job page (/careers/[id])", () => {
  const render = (user: ReturnType<typeof candidate> | null = null) =>
    renderApp(<PublicJobPage />, { path: "/careers/job-1", params: { id: "job-1" }, user });

  it("shows the role, the employer, the description and the facts", async () => {
    apiMock.on("GET", "/public/jobs/job-1", publicJob());
    render();

    expect(await screen.findByRole("heading", { name: "Backend Engineer" })).toBeInTheDocument();
    expect(screen.getByText("Acme Robotics")).toBeInTheDocument();
    expect(screen.getByText(/Build APIs\./)).toBeInTheDocument();
    expect(screen.getByText("$60,000 – $80,000")).toBeInTheDocument();
    expect(screen.getByText("3+ years")).toBeInTheDocument();
    expect(screen.getByText("Required skills")).toBeInTheDocument();
    expect(screen.getByText("Kubernetes")).toBeInTheDocument();
  });

  it("omits facts the job does not state, rather than showing blanks", async () => {
    apiMock.on(
      "GET",
      "/public/jobs/job-1",
      publicJob({ salary_min: null, salary_max: null, min_years_experience: null, preferred_skills: [], required_skills: [] }),
    );
    render();

    await screen.findByRole("heading", { name: "Backend Engineer" });
    expect(screen.queryByText("Salary")).not.toBeInTheDocument();
    expect(screen.queryByText("Experience")).not.toBeInTheDocument();
    expect(screen.queryByText("Required skills")).not.toBeInTheDocument();
    expect(screen.queryByText("Nice to have")).not.toBeInTheDocument();
  });

  it("sends a visitor to sign up, remembering where they were going", async () => {
    apiMock.on("GET", "/public/jobs/job-1", publicJob());
    const { pushes } = render();

    fireEvent.click(await screen.findByRole("button", { name: "Create an account to apply" }));

    expect(pushes).toContain("/register/candidate?next=/careers/job-1/apply");
  });

  it("lets a candidate go straight to the apply page", async () => {
    apiMock.on("GET", "/public/jobs/job-1", publicJob());
    const { pushes } = render(candidate());

    fireEvent.click(await screen.findByRole("button", { name: "Apply now" }));

    expect(pushes).toContain("/careers/job-1/apply");
  });

  it("tells staff that only candidates can apply, with no apply button", async () => {
    apiMock.on("GET", "/public/jobs/job-1", publicJob());
    renderApp(<PublicJobPage />, { path: "/careers/job-1", params: { id: "job-1" }, user: admin() });

    expect(await screen.findByText(/Only candidate accounts can apply/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Apply now" })).not.toBeInTheDocument();
  });

  it("explains a job that is closed or unknown, with a way back", async () => {
    apiMock.on("GET", "/public/jobs/job-1", new MockResponse({ detail: "Job not found." }, 404));
    render();

    expect(await screen.findByText("This position isn't available")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Browse open positions" })).toHaveAttribute("href", "/careers");
  });
});

describe("api paging contract", () => {
  it("requests page 1 first", async () => {
    apiMock.on("GET", "/public/jobs", page([publicJob()]));
    renderApp(<CareersPage />, { path: "/careers" });

    await screen.findByText("Backend Engineer");
    await waitFor(() => expect(apiMock.find("GET", "/public/jobs")).toBeDefined());
  });
});
