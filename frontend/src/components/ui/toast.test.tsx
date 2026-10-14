import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ToastProvider, useToast } from "./toast";

function Triggers() {
  const toast = useToast();
  return (
    <>
      <button onClick={() => toast.success("Saved!")}>success</button>
      <button onClick={() => toast.error("Oops")}>error</button>
    </>
  );
}

const renderToasts = () =>
  render(
    <ToastProvider>
      <Triggers />
    </ToastProvider>,
  );

describe("toasts", () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it("appears when triggered, announced politely to screen readers", () => {
    renderToasts();
    fireEvent.click(screen.getByText("success"));

    expect(screen.getByRole("status")).toHaveTextContent("Saved!");
  });

  it("disappears by itself after four seconds", () => {
    renderToasts();
    fireEvent.click(screen.getByText("success"));

    act(() => void vi.advanceTimersByTime(3999));
    expect(screen.getByText("Saved!")).toBeInTheDocument();
    act(() => void vi.advanceTimersByTime(2));
    expect(screen.queryByText("Saved!")).not.toBeInTheDocument();
  });

  it("keeps an error longer, and announces it assertively", () => {
    renderToasts();
    fireEvent.click(screen.getByText("error"));

    expect(screen.getByRole("alert")).toHaveTextContent("Oops");
    act(() => void vi.advanceTimersByTime(5000));
    expect(screen.getByText("Oops")).toBeInTheDocument();
    act(() => void vi.advanceTimersByTime(2500));
    expect(screen.queryByText("Oops")).not.toBeInTheDocument();
  });

  it("can be dismissed by hand", () => {
    renderToasts();
    fireEvent.click(screen.getByText("success"));

    fireEvent.click(screen.getByLabelText("Dismiss notification"));

    expect(screen.queryByText("Saved!")).not.toBeInTheDocument();
  });

  it("never stacks more than four", () => {
    renderToasts();
    for (let i = 0; i < 6; i++) fireEvent.click(screen.getByText("success"));

    expect(screen.getAllByRole("status")).toHaveLength(4);
  });

  it("refuses to be used outside a provider, with a clear message", () => {
    const spy = vi.spyOn(console, "error").mockImplementation(() => {});
    expect(() => render(<Triggers />)).toThrow(/must be used inside <ToastProvider>/);
    spy.mockRestore();
  });
});
