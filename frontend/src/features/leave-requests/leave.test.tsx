import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { apiMock, MockResponse } from "@/test/api-mock";
import { page } from "@/test/fixtures";
import { admin, employee, renderApp } from "@/test/render-app";
import { LeaveApprovalQueue } from "./components/leave-approval-queue";
import { LeaveApprovalRow } from "./components/leave-approval-row";
import { LeaveBalanceCard } from "./components/leave-balance-card";
import { LeaveRequestForm } from "./components/leave-request-form";
import { MyLeaveRequestsList } from "./components/my-leave-requests-list";
import { formatDateRange, leaveDayCount } from "./lib/format-date-range";

const balance = (used: number, allotment = 20) => ({
  year: 2026,
  annual_allotment: allotment,
  days_used: used,
  days_remaining: allotment - used,
});

const leaveRequest = (id: string, status = "pending", overrides: Record<string, unknown> = {}) => ({
  id,
  employee_id: "e1",
  company_id: "c1",
  start_date: "2026-10-14",
  end_date: "2026-10-18",
  leave_type: "sick",
  reason: "flu",
  status,
  reviewed_by: null,
  reviewed_at: null,
  created_at: "",
  updated_at: "",
  ...overrides,
});

const withEmployee = (lr: ReturnType<typeof leaveRequest>, firstName = "Ada") => ({
  ...lr,
  employee: { id: "e1", first_name: firstName, last_name: "Lovelace", email: "a@b.c", job_title: "Developer", hire_date: "2025-01-01" },
});

describe("date helpers", () => {
  it("counts inclusive calendar days, the way the backend deducts them", () => {
    expect(leaveDayCount("2026-10-14", "2026-10-18")).toBe(5);
    expect(leaveDayCount("2026-10-14", "2026-10-14")).toBe(1);
    expect(leaveDayCount("2026-12-30", "2027-01-02")).toBe(4);
  });

  it("writes a range, showing the year once when both dates share it", () => {
    expect(formatDateRange("2026-10-14", "2026-10-18")).toBe("Oct 14 – Oct 18, 2026");
    expect(formatDateRange("2026-10-14", "2026-10-14")).toBe("Oct 14, 2026");
    expect(formatDateRange("2026-12-30", "2027-01-02")).toBe("Dec 30, 2026 – Jan 2, 2027");
  });
});

describe("LeaveBalanceCard", () => {
  it("shows what remains, what was used, and a bar for the used share", async () => {
    apiMock.on("GET", "/leave-requests/mine/balance", balance(10));
    renderApp(<LeaveBalanceCard />, { user: employee() });

    expect(await screen.findByText("10 of 20 used this year")).toBeInTheDocument();
    expect(screen.getByText(/days remaining/)).toBeInTheDocument();
    const bar = screen.getByRole("img", { name: "10 of 20 leave days used" });
    expect((bar.firstElementChild as HTMLElement).style.width).toBe("50%");
  });

  it("does not hide being over the allotment: warns, and caps the bar at 100%", async () => {
    apiMock.on("GET", "/leave-requests/mine/balance", balance(23));
    renderApp(<LeaveBalanceCard />, { user: employee() });

    expect(await screen.findByText(/3 days over your yearly allotment/)).toBeInTheDocument();
    const bar = screen.getByRole("img");
    expect((bar.firstElementChild as HTMLElement).style.width).toBe("100%");
  });
});

describe("LeaveRequestForm", () => {
  const setup = () => {
    apiMock.on("GET", "/leave-requests/mine/balance", balance(10));
    apiMock.on("POST", "/leave-requests", leaveRequest("new"));
    return renderApp(<LeaveRequestForm />, { user: employee() });
  };
  const fill = (start: string, end: string) => {
    fireEvent.change(screen.getByLabelText("Start date"), { target: { value: start } });
    fireEvent.change(screen.getByLabelText("End date"), { target: { value: end } });
  };

  it("shows no preview before dates are chosen", async () => {
    setup();
    await screen.findByLabelText("Start date");
    expect(screen.queryByText(/if approved/)).not.toBeInTheDocument();
  });

  it("previews the days a request uses and what would remain if approved", async () => {
    setup();
    await screen.findByLabelText("Start date");
    await waitFor(() => expect(apiMock.find("GET", "/leave-requests/mine/balance")).toBeDefined());

    fill("2026-10-14", "2026-10-18");

    expect(await screen.findByText(/5 days/)).toBeInTheDocument();
    expect(screen.getByText(/if approved, you'd have 5 left this year/)).toBeInTheDocument();
  });

  it("warns, without blocking, when a request goes beyond the balance", async () => {
    setup();
    await waitFor(() => expect(apiMock.find("GET", "/leave-requests/mine/balance")).toBeDefined());

    fill("2026-10-14", "2026-10-30");

    expect(await screen.findByText(/17 days/)).toBeInTheDocument();
    expect(screen.getByText(/7 beyond your balance; an admin can still approve it/)).toBeInTheDocument();
  });

  it("does not preview a nonsensical range (end before start)", async () => {
    setup();
    await screen.findByLabelText("Start date");

    fill("2026-10-14", "2026-10-10");

    expect(screen.queryByText(/if approved/)).not.toBeInTheDocument();
  });

  it("says '1 day', not '1 days'", async () => {
    setup();
    await waitFor(() => expect(apiMock.find("GET", "/leave-requests/mine/balance")).toBeDefined());

    fill("2026-10-14", "2026-10-14");

    expect(await screen.findByText("1 day")).toBeInTheDocument();
  });

  it("submits the right payload, confirms with a toast, and clears the form", async () => {
    setup();
    await screen.findByLabelText("Start date");
    fill("2026-10-14", "2026-10-14");
    fireEvent.change(screen.getByLabelText(/Reason/), { target: { value: "Family trip" } });

    fireEvent.click(screen.getByRole("button", { name: "Submit request" }));

    expect(await screen.findByText(/Request submitted/)).toBeInTheDocument();
    expect(apiMock.find("POST", "/leave-requests")?.body).toEqual({
      start_date: "2026-10-14",
      end_date: "2026-10-14",
      leave_type: "vacation",
      reason: "Family trip",
    });
    expect(screen.getByLabelText("Start date")).toHaveValue("");
    expect(screen.getByLabelText(/Reason/)).toHaveValue("");
  });

  it("explains an overlap (409) next to the form", async () => {
    apiMock.on("GET", "/leave-requests/mine/balance", balance(10));
    apiMock.on("POST", "/leave-requests", new MockResponse({ detail: "overlap" }, 409));
    renderApp(<LeaveRequestForm />, { user: employee() });
    await screen.findByLabelText("Start date");
    fill("2026-10-14", "2026-10-15");

    fireEvent.click(screen.getByRole("button", { name: "Submit request" }));

    expect(await screen.findByText(/overlaps a pending or approved leave request/)).toBeInTheDocument();
  });
});

describe("MyLeaveRequestsList", () => {
  const setup = () => {
    apiMock.on("GET", "/leave-requests/mine", page([leaveRequest("lr1"), leaveRequest("lr2", "approved")]));
    apiMock.on("POST", "/leave-requests/lr1/cancel", leaveRequest("lr1", "cancelled"));
    return renderApp(<MyLeaveRequestsList />, { user: employee() });
  };

  it("shows each request's dates, length, type and status", async () => {
    setup();

    expect(await screen.findAllByText("Oct 14 – Oct 18, 2026")).toHaveLength(2);
    expect(screen.getAllByText("5 days")).toHaveLength(2);
    expect(screen.getByText("Pending")).toBeInTheDocument();
    expect(screen.getByText("Approved")).toBeInTheDocument();
  });

  it("only offers Cancel on a pending request", async () => {
    setup();
    await screen.findAllByText("Oct 14 – Oct 18, 2026");

    expect(screen.getAllByRole("button", { name: "Cancel" })).toHaveLength(1);
  });

  it("asks before cancelling, and sends nothing until confirmed", async () => {
    setup();
    fireEvent.click(await screen.findByRole("button", { name: "Cancel" }));

    expect(screen.getByRole("button", { name: "Cancel request" })).toBeInTheDocument();
    expect(apiMock.writes).toHaveLength(0);

    fireEvent.click(screen.getByRole("button", { name: "Keep it" }));
    expect(screen.queryByRole("button", { name: "Cancel request" })).not.toBeInTheDocument();
    expect(apiMock.writes).toHaveLength(0);
  });

  it("cancels once confirmed, and says so", async () => {
    setup();
    fireEvent.click(await screen.findByRole("button", { name: "Cancel" }));
    fireEvent.click(screen.getByRole("button", { name: "Cancel request" }));

    expect(await screen.findByText("Leave request cancelled")).toBeInTheDocument();
    expect(apiMock.find("POST", "/leave-requests/lr1/cancel")).toBeDefined();
  });

  it("explains an empty list", async () => {
    apiMock.on("GET", "/leave-requests/mine", page([]));
    renderApp(<MyLeaveRequestsList />, { user: employee() });

    expect(await screen.findByText("No leave requests yet")).toBeInTheDocument();
  });
});

describe("LeaveApprovalRow", () => {
  const setup = () => {
    apiMock.on("POST", "/leave-requests/lr1/approve", leaveRequest("lr1", "approved"));
    apiMock.on("POST", "/leave-requests/lr1/reject", leaveRequest("lr1", "rejected"));
    return renderApp(
      <ul>
        <LeaveApprovalRow leaveRequest={withEmployee(leaveRequest("lr1")) as never} />
      </ul>,
      { user: admin() },
    );
  };

  it("shows who asked, for what, when, and how long", async () => {
    setup();

    expect(await screen.findByText(/Ada Lovelace/)).toBeInTheDocument();
    expect(screen.getByText("Oct 14 – Oct 18, 2026")).toBeInTheDocument();
    expect(screen.getByText("5 days")).toBeInTheDocument();
    expect(screen.getByText("flu")).toBeInTheDocument();
  });

  it("approves in one click and confirms with a toast", async () => {
    setup();
    fireEvent.click(await screen.findByRole("button", { name: "Approve" }));

    expect(await screen.findByText("Approved Ada's request")).toBeInTheDocument();
    expect(apiMock.find("POST", "/leave-requests/lr1/approve")).toBeDefined();
  });

  it("makes rejecting a two-step action", async () => {
    setup();
    fireEvent.click(await screen.findByRole("button", { name: "Reject" }));

    expect(screen.getByText("Reject this request?")).toBeInTheDocument();
    expect(apiMock.writes).toHaveLength(0);

    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(screen.getByRole("button", { name: "Approve" })).toBeInTheDocument();
    expect(apiMock.writes).toHaveLength(0);

    fireEvent.click(screen.getByRole("button", { name: "Reject" }));
    fireEvent.click(screen.getByRole("button", { name: "Confirm" }));
    expect(await screen.findByText("Rejected Ada's request")).toBeInTheDocument();
  });
});

describe("LeaveApprovalQueue", () => {
  let pending = 21;
  const setup = () => {
    apiMock.on("GET", "/leave-requests", (call) => {
      const q = new URLSearchParams(call.search);
      const status = q.get("status");
      const pageNumber = Number(q.get("page") ?? 1);
      const size = Number(q.get("page_size") ?? 20);
      const total = status === "pending" || status === null ? pending : 0;
      const start = (pageNumber - 1) * size;
      const count = size === 1 ? 0 : Math.max(0, Math.min(size, total - start));
      const items = Array.from({ length: count }, (_, i) =>
        withEmployee(leaveRequest(`lr${start + i}`), `Emp${start + i}`),
      );
      return page(items, total, pageNumber, size);
    });
    apiMock.on("POST", /\/leave-requests\/lr\d+\/approve/, leaveRequest("x", "approved"));
    return renderApp(<LeaveApprovalQueue />, { user: admin() });
  };

  it("summarises what is waiting and shows real counts on the tabs", async () => {
    pending = 21;
    setup();

    expect(await screen.findByText(/requests are/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Pending/ })).toHaveTextContent("21");
    expect(screen.getByRole("button", { name: /Approved/ })).toHaveTextContent("0");
  });

  it("pages through requests instead of hiding everything past the first 20", async () => {
    pending = 21;
    setup();
    expect(await screen.findByText("Page 1 of 2")).toBeInTheDocument();
    expect(screen.getByText(/Emp0 /)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Next" }));

    expect(await screen.findByText("Page 2 of 2")).toBeInTheDocument();
    expect(screen.getByText(/Emp20 /)).toBeInTheDocument();
  });

  it("steps back to a real page when acting on the last row of the last page", async () => {
    pending = 21;
    setup();
    fireEvent.click(await screen.findByRole("button", { name: "Next" }));
    await screen.findByText(/Emp20 /);

    pending = 20; // that last request is handled: page 2 no longer exists
    fireEvent.click(screen.getByRole("button", { name: "Approve" }));

    expect(await screen.findByText(/Emp0 /)).toBeInTheDocument();
    expect(screen.queryByText(/all caught up/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Page 2 of/)).not.toBeInTheDocument();
  });

  it("explains an empty queue", async () => {
    pending = 0;
    setup();

    expect(await screen.findByText("You're all caught up")).toBeInTheDocument();
  });

  it("filters by tab", async () => {
    pending = 3;
    setup();
    await screen.findByText(/Emp0 /);

    fireEvent.click(screen.getByRole("button", { name: /Approved/ }));

    expect(await screen.findByText("Nothing approved yet")).toBeInTheDocument();
    const list = screen.queryByRole("list");
    if (list) expect(within(list).queryAllByText(/Emp/)).toHaveLength(0);
  });
});
