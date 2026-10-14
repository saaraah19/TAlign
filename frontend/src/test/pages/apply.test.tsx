import { fireEvent, screen, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import ApplyPage from "@/app/(public)/careers/[id]/apply/page";
import { apiMock, MockResponse } from "../api-mock";
import { publicJob, resume } from "../fixtures";
import { candidate, recruiter, renderApp } from "../render-app";

const render = (user: ReturnType<typeof candidate> | ReturnType<typeof recruiter> | null) =>
  renderApp(<ApplyPage />, { path: "/careers/job-1/apply", params: { id: "job-1" }, user });

function chooseFile(container: HTMLElement, name = "cv.pdf") {
  const input = container.querySelector('input[type="file"]') as HTMLInputElement;
  const file = new File(["%PDF-1.4"], name, { type: "application/pdf" });
  fireEvent.change(input, { target: { files: [file] } });
}

describe("apply page", () => {
  it("sends a signed-out visitor to sign up and brings them back here", async () => {
    apiMock.on("GET", "/public/jobs/job-1", publicJob());
    const { pushes } = render(null);

    await waitFor(() => expect(pushes).toContain("replace:/register/candidate?next=/careers/job-1/apply"));
  });

  it("tells a company account that only candidates can apply", async () => {
    apiMock.on("GET", "/public/jobs/job-1", publicJob());
    render(recruiter());

    expect(await screen.findByText("Only candidate accounts can apply")).toBeInTheDocument();
  });

  describe("as a candidate with saved resumes", () => {
    const setup = () => {
      apiMock.on("GET", "/public/jobs/job-1", publicJob());
      apiMock.on("GET", "/resumes/mine", [resume("r1", "old-cv.pdf"), resume("r2", "broken.pdf", "parse_failed")]);
      apiMock.on("POST", "/applications", { id: "app-1" });
      apiMock.on("PUT", "/applications/mine/app-1/resume", { id: "app-1" });
      return render(candidate());
    };

    it("shows the role with its employer and the saved resumes with their size", async () => {
      setup();

      expect(await screen.findByText("Apply to Backend Engineer")).toBeInTheDocument();
      expect(screen.getByText(/Acme Robotics · Full-time/)).toBeInTheDocument();
      expect(await screen.findByText("old-cv.pdf")).toBeInTheDocument();
      expect(screen.getByText(/2 KB/)).toBeInTheDocument();
    });

    it("keeps Submit disabled until a resume is chosen", async () => {
      setup();
      await screen.findByText("old-cv.pdf");

      expect(screen.getByRole("button", { name: "Submit application" })).toBeDisabled();
    });

    it("disables a resume that could not be read, and says why", async () => {
      setup();
      await screen.findByText("broken.pdf");

      expect(screen.getByRole("button", { name: /broken\.pdf/ })).toBeDisabled();
      expect(screen.getByText(/Could not be read/)).toBeInTheDocument();
    });

    it("is open about AI involvement and about who decides", async () => {
      setup();

      expect(await screen.findByText(/An AI reads your resume/)).toBeInTheDocument();
      expect(screen.getByText(/decision is made by a person/)).toBeInTheDocument();
    });

    it("sends nothing until Submit, then applies and attaches the chosen resume", async () => {
      const { pushes } = setup();
      fireEvent.click(await screen.findByRole("button", { name: /old-cv\.pdf/ }));

      expect(screen.getByRole("button", { name: "Submit application" })).toBeEnabled();
      expect(apiMock.writes).toHaveLength(0); // choosing is local until submit

      fireEvent.click(screen.getByRole("button", { name: "Submit application" }));

      await waitFor(() => expect(pushes).toContain("/applications/app-1"));
      expect(apiMock.find("POST", "/applications")?.body).toEqual({ job_id: "job-1" });
      expect(apiMock.find("PUT", "/applications/mine/app-1/resume")?.body).toEqual({ resume_id: "r1" });
      expect(await screen.findByText("Application submitted")).toBeInTheDocument();
    });
  });

  describe("as a candidate with no saved resume", () => {
    it("uploads a file, selects it automatically and then submits", async () => {
      apiMock.on("GET", "/public/jobs/job-1", publicJob());
      apiMock.on("GET", "/resumes/mine", []);
      apiMock.on("POST", "/resumes", new MockResponse(resume("r-new", "cv.pdf"), 201));
      apiMock.on("POST", "/applications", { id: "app-1" });
      apiMock.on("PUT", "/applications/mine/app-1/resume", { id: "app-1" });
      const { container, pushes } = render(candidate());

      expect(await screen.findByText("Upload your resume")).toBeInTheDocument();
      expect(screen.queryByText(/already uploaded/)).not.toBeInTheDocument();

      chooseFile(container);

      await waitFor(() => expect(screen.getByRole("button", { name: "Submit application" })).toBeEnabled());
      expect(apiMock.find("POST", "/resumes")).toBeDefined();

      fireEvent.click(screen.getByRole("button", { name: "Submit application" }));
      await waitFor(() => expect(pushes).toContain("/applications/app-1"));
      expect(apiMock.find("PUT", "/applications/mine/app-1/resume")?.body).toEqual({ resume_id: "r-new" });
    });

    it("explains an upload the server refuses and stays usable", async () => {
      apiMock.on("GET", "/public/jobs/job-1", publicJob());
      apiMock.on("GET", "/resumes/mine", []);
      apiMock.on("POST", "/resumes", new MockResponse({ detail: "That file type isn't supported." }, 415));
      const { container } = render(candidate());
      await screen.findByText("Upload your resume");

      chooseFile(container, "cv.exe");

      expect(await screen.findByText("That file type isn't supported.")).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Submit application" })).toBeDisabled();
    });

    it("shows a clear message if the candidate already applied (409) and keeps the form usable", async () => {
      apiMock.on("GET", "/public/jobs/job-1", publicJob());
      apiMock.on("GET", "/resumes/mine", [resume("r1", "old-cv.pdf")]);
      apiMock.on("POST", "/applications", new MockResponse({ detail: "duplicate" }, 409));
      const { pushes } = render(candidate());

      fireEvent.click(await screen.findByRole("button", { name: /old-cv\.pdf/ }));
      fireEvent.click(screen.getByRole("button", { name: "Submit application" }));

      expect(await screen.findByText(/already applied to this role/)).toBeInTheDocument();
      expect(pushes.filter((p) => p.startsWith("/applications/"))).toHaveLength(0);
      expect(screen.getByRole("button", { name: "Submit application" })).toBeEnabled();
    });
  });
});
