import { fireEvent, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { apiMock, MockResponse } from "@/test/api-mock";
import { candidate, renderApp } from "@/test/render-app";
import { LoginForm } from "./login-form";

const signIn = () => {
  fireEvent.change(screen.getByLabelText("Email"), { target: { value: "sam@example.com" } });
  fireEvent.change(screen.getByLabelText("Password"), { target: { value: "Password123!" } });
  fireEvent.click(screen.getByRole("button", { name: "Sign in" }));
};

describe("LoginForm", () => {
  it("signs in and tells its owner", async () => {
    const onSuccess = vi.fn();
    apiMock.on("POST", "/auth/login", {
      access_token: "token",
      token_type: "bearer",
      expires_in: 1800,
      user: candidate(),
    });
    renderApp(<LoginForm onSuccess={onSuccess} />);

    signIn();

    await waitFor(() => expect(onSuccess).toHaveBeenCalled());
    expect(apiMock.find("POST", "/auth/login")?.body).toEqual({ email: "sam@example.com", password: "Password123!" });
  });

  it("shows the server's message for a wrong password", async () => {
    apiMock.on("POST", "/auth/login", new MockResponse({ detail: "Invalid email or password." }, 401));
    renderApp(<LoginForm />);

    signIn();

    expect(await screen.findByText("Invalid email or password.")).toBeInTheDocument();
  });

  it("shows the throttling message, with the wait, when too many attempts failed", async () => {
    apiMock.on(
      "POST",
      "/auth/login",
      new MockResponse({ detail: "Too many failed sign-in attempts. Try again in 12 minutes." }, 429, { "retry-after": "720" }),
    );
    renderApp(<LoginForm />);

    signIn();

    expect(await screen.findByText(/Too many failed sign-in attempts. Try again in 12 minutes./)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Sign in" })).toBeEnabled(); // the form stays usable
  });

  it("falls back to a generic message for an unexpected failure", async () => {
    apiMock.on("POST", "/auth/login", () => {
      throw new TypeError("network down");
    });
    renderApp(<LoginForm />);

    signIn();

    expect(await screen.findByText("Something went wrong.")).toBeInTheDocument();
  });
});
