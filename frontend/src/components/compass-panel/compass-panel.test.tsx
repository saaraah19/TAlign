import { act, fireEvent, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { apiMock } from "@/test/api-mock";
import { admin, candidate, employee, makeUser, recruiter, renderApp } from "@/test/render-app";
import { CompassPanel } from "./compass-panel";
import { CompassPanelProvider, useCompassPanel } from "./compass-panel-provider";
import { availableCompassScopes, type CompassScope } from "./compass-scope";

const UUID = "11111111-2222-3333-4444-555555555555";
const staffScope: CompassScope = { kind: "application", applicationId: UUID, audience: "staff" };
const candidateScope: CompassScope = { kind: "application", applicationId: UUID, audience: "candidate" };
const company: CompassScope = { kind: "company" };

const doc = (id: string, title: string, status: string) => ({ id, title, status, category: "policy" });
const documents = (...items: ReturnType<typeof doc>[]) => ({ items, total: items.length, page: 1, page_size: 100 });

describe("who may ask Compass what, from which page", () => {
  const describeScopes = (user: Parameters<typeof availableCompassScopes>[0], path: string) =>
    availableCompassScopes(user, path).map((s) => (s.kind === "application" ? `application:${s.audience}` : s.kind));

  it("lets a candidate ask only about their own application, on that page", () => {
    expect(describeScopes(candidate(), `/applications/${UUID}`)).toEqual(["application:candidate"]);
  });

  it("offers a candidate nothing elsewhere — they have no access to policies", () => {
    expect(describeScopes(candidate(), "/dashboard")).toEqual([]);
    expect(describeScopes(candidate(), "/careers")).toEqual([]);
    expect(describeScopes(candidate(), `/pipeline/${UUID}`)).toEqual([]);
  });

  it("offers staff the candidate's analysis on a candidate page, plus company policies", () => {
    expect(describeScopes(recruiter(), `/pipeline/${UUID}`)).toEqual(["application:staff", "company"]);
  });

  it("offers staff company policies everywhere else", () => {
    expect(describeScopes(recruiter(), "/dashboard")).toEqual(["company"]);
    expect(describeScopes(recruiter(), "/pipeline")).toEqual(["company"]);
  });

  it("ignores paths that only look like a candidate page", () => {
    expect(describeScopes(recruiter(), "/pipeline/new")).toEqual(["company"]);
    expect(describeScopes(recruiter(), `/pipeline/${UUID}/extra`)).toEqual(["company"]);
  });

  it("tolerates a trailing slash and an upper-case id", () => {
    expect(describeScopes(recruiter(), `/pipeline/${UUID.toUpperCase()}/`)).toEqual(["application:staff", "company"]);
  });

  it("gives a plain employee company policies only, even on a pipeline URL", () => {
    expect(describeScopes(employee(), "/knowledge")).toEqual(["company"]);
    expect(describeScopes(employee(), `/pipeline/${UUID}`)).toEqual(["company"]);
  });

  it("treats an admin who is also an employee as staff", () => {
    expect(describeScopes(makeUser("internal", ["admin", "employee"]), `/pipeline/${UUID}`)).toEqual([
      "application:staff",
      "company",
    ]);
  });

  it("offers nothing to an account with no roles", () => {
    expect(describeScopes(makeUser("internal", []), "/dashboard")).toEqual([]);
  });
});

describe("CompassPanel", () => {
  it("opens as a modal, locks page scroll and focuses the question box", () => {
    renderApp(<CompassPanel isOpen onClose={() => {}} scopes={[staffScope]} />, { user: recruiter() });

    expect(document.querySelector("dialog")).toHaveAttribute("open");
    expect(document.body.style.overflow).toBe("hidden");
    expect(screen.getByRole("textbox")).toHaveFocus(); // not the close button
  });

  it("renders nothing and does not lock scroll while closed", () => {
    renderApp(<CompassPanel isOpen={false} onClose={() => {}} scopes={[staffScope]} />, { user: recruiter() });

    expect(document.querySelector("dialog")).not.toHaveAttribute("open");
    expect(screen.queryByText("Ask Compass")).not.toBeInTheDocument();
    expect(document.body.style.overflow).not.toBe("hidden");
  });

  it("offers staff questions that the stored analysis can actually answer", () => {
    renderApp(<CompassPanel isOpen onClose={() => {}} scopes={[staffScope]} />, { user: recruiter() });

    expect(screen.getByText("Why this score?")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Ask about this candidate…")).toBeInTheDocument();
  });

  it("words things for a candidate asking about their own application", () => {
    renderApp(<CompassPanel isOpen onClose={() => {}} scopes={[candidateScope]} />, { user: candidate() });

    expect(screen.getByText("What stage is my application at?")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Ask about your application…")).toBeInTheDocument();
  });

  it("sends the question with the application it is about, and shows the answer", async () => {
    apiMock.on("POST", "/compass/ask", { message: "Because the Python match is strong.", citations: null, confidence: null });
    renderApp(<CompassPanel isOpen onClose={() => {}} scopes={[staffScope]} />, { user: recruiter() });

    fireEvent.click(screen.getByText("Why this score?"));

    expect(await screen.findByText("Because the Python match is strong.")).toBeInTheDocument();
    expect(apiMock.find("POST", "/compass/ask")?.body).toMatchObject({ message: "Why this score?", application_id: UUID });
  });

  it("closes on a click on the dimmed area but not on a click inside", () => {
    const onClose = vi.fn();
    renderApp(<CompassPanel isOpen onClose={onClose} scopes={[staffScope]} />, { user: recruiter() });
    const dialog = document.querySelector("dialog") as HTMLDialogElement;

    fireEvent.click(screen.getByText("Why this score?").closest("div") as HTMLElement);
    expect(onClose).not.toHaveBeenCalled();

    fireEvent.click(dialog);
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("reports Esc (the browser's native close) to its owner", () => {
    const onClose = vi.fn();
    renderApp(<CompassPanel isOpen onClose={onClose} scopes={[staffScope]} />, { user: recruiter() });

    act(() => (document.querySelector("dialog") as HTMLDialogElement).close());

    expect(onClose).toHaveBeenCalled();
  });

  it("restores page scrolling when it goes away", () => {
    const { unmount } = renderApp(<CompassPanel isOpen onClose={() => {}} scopes={[staffScope]} />, { user: recruiter() });
    unmount();

    expect(document.body.style.overflow).not.toBe("hidden");
  });

  describe("company questions", () => {
    it("suggests questions only from documents that are ready", async () => {
      apiMock.on("GET", "/knowledge/documents", documents(doc("1", "Remote Work Policy", "ready"), doc("2", "Pending Doc", "embedded")));
      renderApp(<CompassPanel isOpen onClose={() => {}} scopes={[company]} />, { user: recruiter() });

      expect(await screen.findByText("What does “Remote Work Policy” cover?")).toBeInTheDocument();
      expect(screen.queryByText(/Pending Doc/)).not.toBeInTheDocument();
    });

    it("focuses the question box once the documents have loaded", async () => {
      apiMock.on("GET", "/knowledge/documents", documents(doc("1", "Leave Policy", "ready")));
      renderApp(<CompassPanel isOpen onClose={() => {}} scopes={[company]} />, { user: recruiter() });

      await screen.findByText(/Leave Policy/);
      await waitFor(() => expect(screen.getByRole("textbox")).toHaveFocus());
    });

    it("says there is nothing to answer from, and points to the Knowledge Center, when no document is ready", async () => {
      apiMock.on("GET", "/knowledge/documents", documents(doc("2", "Pending Doc", "embedded")));
      const onClose = vi.fn();
      renderApp(<CompassPanel isOpen onClose={onClose} scopes={[company]} />, { user: recruiter() });

      expect(await screen.findByText(/no documents to answer from yet/)).toBeInTheDocument();
      expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
      fireEvent.click(screen.getByRole("link", { name: "Open the Knowledge Center" }));
      expect(onClose).toHaveBeenCalled();
    });
  });

  it("lets staff switch between the candidate and company questions", async () => {
    apiMock.on("GET", "/knowledge/documents", documents(doc("1", "Leave Policy", "ready")));
    renderApp(<CompassPanel isOpen onClose={() => {}} scopes={[staffScope, company]} />, { user: recruiter() });

    expect(screen.getByText("Why this score?")).toBeInTheDocument(); // candidate first

    fireEvent.click(screen.getByRole("button", { name: "Company policies" }));
    expect(await screen.findByText(/Leave Policy/)).toBeInTheDocument();
    expect(screen.queryByText("Why this score?")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "This candidate" }));
    expect(screen.getByText("Why this score?")).toBeInTheDocument();
  });

  it("shows no switcher when there is only one thing to ask about", () => {
    renderApp(<CompassPanel isOpen onClose={() => {}} scopes={[staffScope]} />, { user: recruiter() });

    expect(screen.queryByRole("group", { name: "What to ask about" })).not.toBeInTheDocument();
  });
});

describe("CompassPanelProvider", () => {
  function Consumer() {
    const compass = useCompassPanel();
    return (
      <>
        <span data-testid="can">{String(compass.canAsk)}</span>
        <span data-testid="label">{compass.shortcutLabel}</span>
        <button onClick={compass.open}>open-compass</button>
      </>
    );
  }
  const renderProvider = (user: Parameters<typeof renderApp>[1] extends infer O ? (O extends { user?: infer U } ? U : never) : never, path = "/dashboard") => {
    apiMock.on("GET", "/knowledge/documents", documents());
    return renderApp(
      <CompassPanelProvider>
        <Consumer />
      </CompassPanelProvider>,
      { user, path },
    );
  };
  const press = (init: KeyboardEventInit) => act(() => void window.dispatchEvent(new KeyboardEvent("keydown", { bubbles: true, cancelable: true, ...init })));
  const isOpen = () => document.querySelector("dialog")?.hasAttribute("open") ?? false;

  it("lets staff ask, and toggles with Ctrl/Cmd+K in either letter case", async () => {
    renderProvider(recruiter());
    await waitFor(() => expect(screen.getByTestId("can")).toHaveTextContent("true"));
    expect(screen.getByTestId("label")).toHaveTextContent("Ctrl K");
    expect(isOpen()).toBe(false);

    press({ key: "k", ctrlKey: true });
    await waitFor(() => expect(isOpen()).toBe(true));

    press({ key: "K", metaKey: true });
    await waitFor(() => expect(isOpen()).toBe(false));
  });

  it("ignores a plain 'k'", async () => {
    renderProvider(recruiter());
    await waitFor(() => expect(screen.getByTestId("can")).toHaveTextContent("true"));

    press({ key: "k" });

    expect(isOpen()).toBe(false);
  });

  it("opens from a button too", async () => {
    renderProvider(recruiter());
    await waitFor(() => expect(screen.getByTestId("can")).toHaveTextContent("true"));

    fireEvent.click(screen.getByText("open-compass"));

    await waitFor(() => expect(isOpen()).toBe(true));
  });

  it("closes when the user navigates elsewhere", async () => {
    const { navigate } = renderProvider(recruiter());
    await waitFor(() => expect(screen.getByTestId("can")).toHaveTextContent("true"));
    fireEvent.click(screen.getByText("open-compass"));
    await waitFor(() => expect(isOpen()).toBe(true));

    await navigate(`/pipeline/${UUID}`);

    await waitFor(() => expect(isOpen()).toBe(false));
  });

  it("offers a candidate nothing off their application: no shortcut, no panel", async () => {
    renderProvider(candidate());
    await waitFor(() => expect(screen.getByTestId("can")).toBeInTheDocument());
    await waitFor(() => expect(apiMock.find("GET", "/auth/me")).toBeDefined());

    expect(screen.getByTestId("can")).toHaveTextContent("false");
    press({ key: "k", ctrlKey: true });
    expect(document.querySelector("dialog")).toBeNull();
  });

  it("offers a candidate only their own application, on its page", async () => {
    renderProvider(candidate(), `/applications/${UUID}`);
    await waitFor(() => expect(screen.getByTestId("can")).toHaveTextContent("true"));

    press({ key: "k", ctrlKey: true });

    await waitFor(() => expect(isOpen()).toBe(true));
    expect(screen.getByText("What stage is my application at?")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Company policies" })).not.toBeInTheDocument();
  });

  it("does not leak the admin helper into a visitor's session", async () => {
    renderProvider(null);
    await waitFor(() => expect(apiMock.find("POST", "/auth/refresh")).toBeDefined());

    expect(screen.getByTestId("can")).toHaveTextContent("false");
    void admin; // (imported for symmetry with the other role cases)
  });
});
