import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { apiMock } from "@/test/api-mock";
import { recruiter, renderApp } from "@/test/render-app";
import { EmailDraftCard } from "@/features/communication/components/email-draft-card";
import { ScoreGauge } from "../analysis/score-gauge";
import { SkillEvidenceList } from "../analysis/skill-evidence-list";
import { ApplicationStatusBadge } from "../application-status-badge";
import { StageActions } from "./stage-actions";
import { StageJourney } from "./stage-journey";

describe("StageJourney", () => {
  it("marks the current stage and the path behind it", () => {
    render(<StageJourney status="interview" />);

    expect(screen.getByText("Current stage")).toBeInTheDocument();
    expect(screen.getAllByRole("listitem")).toHaveLength(5);
  });

  it("shows no current stage once hired", () => {
    render(<StageJourney status="hired" />);

    expect(screen.queryByText("Current stage")).not.toBeInTheDocument();
  });

  it("words a rejection for staff and for the candidate differently", () => {
    const { unmount } = render(<StageJourney status="rejected" audience="staff" />);
    expect(screen.getByText("This candidate is no longer in the pipeline.")).toBeInTheDocument();
    unmount();

    render(<StageJourney status="rejected" audience="candidate" />);
    expect(screen.getByText("Not moving forward")).toBeInTheDocument();
    expect(screen.queryByText(/This candidate/)).not.toBeInTheDocument();
  });
});

describe("ApplicationStatusBadge", () => {
  it("gives each stage a distinct, consistent look", () => {
    const classFor = (status: Parameters<typeof ApplicationStatusBadge>[0]["status"]) => {
      const { container, unmount } = render(<ApplicationStatusBadge status={status} />);
      const cls = container.firstElementChild?.className ?? "";
      unmount();
      return cls;
    };

    expect(classFor("interview")).toContain("text-accent-dim");
    expect(classFor("screening")).toContain("text-blue-700");
    expect(classFor("rejected")).toContain("text-red-600");
    expect(new Set(["applied", "screening", "interview", "offer", "hired", "rejected"].map((s) => classFor(s as never))).size).toBe(6);
  });
});

describe("StageActions", () => {
  const setup = (status: "applied" | "offer" | "hired") => {
    apiMock.on("POST", "/applications/app-1/transition", { id: "app-1" });
    return renderApp(<StageActions applicationId="app-1" status={status} />, { user: recruiter() });
  };

  it("offers the one legal next step and a rejection", () => {
    setup("applied");

    expect(screen.getByRole("button", { name: "Move to Screening" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reject" })).toBeInTheDocument();
  });

  it("offers nothing once a candidate is hired", () => {
    setup("hired");

    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("asks before rejecting, and sends nothing until confirmed", () => {
    setup("applied");
    fireEvent.click(screen.getByRole("button", { name: "Reject" }));

    expect(screen.getByText("Reject this candidate? This can't be undone.")).toBeInTheDocument();
    expect(apiMock.writes).toHaveLength(0);

    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(screen.getByRole("button", { name: "Reject" })).toBeInTheDocument();
    expect(apiMock.writes).toHaveLength(0);
  });

  it("rejects once confirmed, and confirms with a toast", async () => {
    setup("applied");
    fireEvent.click(screen.getByRole("button", { name: "Reject" }));
    fireEvent.click(screen.getByRole("button", { name: "Confirm reject" }));

    expect(await screen.findByText("Application rejected")).toBeInTheDocument();
    expect(apiMock.find("POST", "/applications/app-1/transition")?.body).toEqual({ target_status: "rejected" });
  });

  it("advances in one click", async () => {
    setup("applied");
    fireEvent.click(screen.getByRole("button", { name: "Move to Screening" }));

    expect(await screen.findByText("Moved to Screening")).toBeInTheDocument();
  });
});

describe("EmailDraftCard", () => {
  const email = {
    id: "e1",
    application_id: "app-1",
    email_type: "rejection",
    status: "draft",
    recipient_email: "a@b.c",
    subject: "Hi",
    body: "Body",
    llm_provider: "gemini",
    llm_model: "m",
    prompt_version: null,
    sent_at: null,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };

  it("reads like a composer and is honest that Talign does not send email", () => {
    apiMock.on("POST", "/applications/app-1/emails/e1/send", { ...email, status: "sent" });
    renderApp(<EmailDraftCard applicationId="app-1" email={email as never} />, { user: recruiter() });

    expect(screen.getByText("a@b.c")).toBeInTheDocument();
    expect(screen.getByText(/doesn't send email/)).toBeInTheDocument();
    expect(screen.getByText(/Drafted by Compass/)).toBeInTheDocument();
  });

  it("records that the recruiter sent it, with a toast", async () => {
    apiMock.on("POST", "/applications/app-1/emails/e1/send", { ...email, status: "sent" });
    renderApp(<EmailDraftCard applicationId="app-1" email={email as never} />, { user: recruiter() });

    fireEvent.click(screen.getByRole("button", { name: "Mark as sent" }));

    expect(await screen.findByText("Email marked as sent")).toBeInTheDocument();
  });

  it("is read-only once sent", () => {
    renderApp(<EmailDraftCard applicationId="app-1" email={{ ...email, status: "sent", sent_at: new Date().toISOString() } as never} />, { user: recruiter() });

    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Mark as sent" })).not.toBeInTheDocument();
  });
});

describe("Resume Intelligence components", () => {
  it("labels the score by band and shows the number", () => {
    const { unmount } = render(<ScoreGauge score={85} />);
    expect(screen.getByText("Strong alignment")).toBeInTheDocument();
    unmount();
    const second = render(<ScoreGauge score={65} />);
    expect(screen.getByText("Moderate alignment")).toBeInTheDocument();
    second.unmount();
    render(<ScoreGauge score={40} />);
    expect(screen.getByText("Limited alignment")).toBeInTheDocument();
  });

  it("does not invent a score that does not exist", () => {
    render(<ScoreGauge score={null} />);

    expect(screen.getByText("No score")).toBeInTheDocument();
  });

  it("summarises skills and collapses long lists", () => {
    const matches = Array.from({ length: 8 }, (_, i) => ({
      skill: `Skill ${i}`,
      match_state: (["matched", "not_matched", "insufficient_evidence"] as const)[i % 3],
      evidence: "",
    }));
    render(<SkillEvidenceList title="Required skills" matches={matches as never} />);

    expect(screen.getByText("3 of 8 matched")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Show 2 more" })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Show 2 more" }));
    expect(screen.getByText("Skill 7")).toBeInTheDocument();
  });
});
