import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import ApplicationsPage from "@/app/(protected)/applications/page";
import MyApplicationPage from "@/app/(protected)/applications/[id]/page";
import { apiMock } from "../api-mock";
import { page } from "../fixtures";
import { candidate, renderApp } from "../render-app";

const application = (status = "interview") => ({
  id: "app-1",
  status,
  created_at: new Date().toISOString(),
  job: { id: "job-1", title: "Backend Engineer", company_id: "company-1" },
});

describe("My applications", () => {
  it("lists each application with a link and its status", async () => {
    apiMock.on("GET", "/applications/mine", page([application()]));
    renderApp(<ApplicationsPage />, { path: "/applications", user: candidate() });

    expect(await screen.findByText("Backend Engineer")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Backend Engineer/ })).toHaveAttribute("href", "/applications/app-1");
    expect(screen.getByText("Interview")).toBeInTheDocument();
  });

  it("invites a candidate with none to browse open positions", async () => {
    apiMock.on("GET", "/applications/mine", page([]));
    renderApp(<ApplicationsPage />, { path: "/applications", user: candidate() });

    expect(await screen.findByText("No applications yet")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Browse open positions" })).toHaveAttribute("href", "/careers");
  });
});

describe("a single application (candidate view)", () => {
  const render = (id = "app-1") =>
    renderApp(<MyApplicationPage />, { path: `/applications/${id}`, params: { id }, user: candidate() });

  it("shows the role, the status and where the candidate stands", async () => {
    apiMock.on("GET", "/applications/mine", page([application("interview")]));
    apiMock.on("GET", "/applications/mine/app-1/analysis-status", { status: "analyzing" });
    apiMock.on("GET", "/resumes/mine", []);
    render();

    expect(await screen.findByRole("heading", { name: "Backend Engineer" })).toBeInTheDocument();
    expect(screen.getByText("Where you are")).toBeInTheDocument();
    expect(screen.getByText("Current stage")).toBeInTheDocument();
  });

  it("shows only the progress of the automated review, never a score", async () => {
    apiMock.on("GET", "/applications/mine", page([application()]));
    apiMock.on("GET", "/applications/mine/app-1/analysis-status", { status: "analyzing" });
    apiMock.on("GET", "/resumes/mine", []);
    render();

    expect(await screen.findByText(/analy/i)).toBeInTheDocument();
    expect(screen.queryByText(/score/i)).not.toBeInTheDocument();
  });

  it("words the Compass box for the candidate and offers a real question", async () => {
    apiMock.on("GET", "/applications/mine", page([application()]));
    apiMock.on("GET", "/applications/mine/app-1/analysis-status", { status: "not_started" });
    apiMock.on("GET", "/resumes/mine", []);
    render();

    expect(await screen.findByPlaceholderText("Ask about your application…")).toBeInTheDocument();
    expect(screen.getByText("What stage is my application at?")).toBeInTheDocument();
  });

  it("uses candidate-appropriate wording when the application was not successful", async () => {
    apiMock.on("GET", "/applications/mine", page([application("rejected")]));
    apiMock.on("GET", "/applications/mine/app-1/analysis-status", { status: "complete" });
    apiMock.on("GET", "/resumes/mine", []);
    render();

    expect(await screen.findByText("Not moving forward")).toBeInTheDocument();
    expect(screen.queryByText(/This candidate/)).not.toBeInTheDocument();
  });

  it("explains an unknown application with a way back", async () => {
    apiMock.on("GET", "/applications/mine", page([application()]));
    render("does-not-exist");

    expect(await screen.findByText("Application not found")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Back to my applications" })).toHaveAttribute("href", "/applications");
  });
});
