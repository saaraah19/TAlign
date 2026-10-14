import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { admin, candidate, renderApp } from "@/test/render-app";
import { PublicHeader } from "./public-header";

describe("PublicHeader", () => {
  it("offers sign-in and sign-up to a visitor", async () => {
    renderApp(<PublicHeader />, { path: "/careers" });

    expect(await screen.findByRole("link", { name: "Sign in" })).toHaveAttribute("href", "/login");
    expect(screen.getByRole("link", { name: "Create account" })).toHaveAttribute(
      "href",
      "/register/candidate",
    );
  });

  it("shows the brand and highlights the job board while browsing it", async () => {
    renderApp(<PublicHeader />, { path: "/careers" });

    expect(await screen.findByText("TALIGN")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Open positions" }).className).toContain("bg-ink/[0.06]");
  });

  it("sends a signed-in candidate back to their applications, with no sign-in prompt", async () => {
    renderApp(<PublicHeader />, { path: "/careers/x", user: candidate() });

    expect(await screen.findByRole("link", { name: "My applications" })).toHaveAttribute(
      "href",
      "/applications",
    );
    expect(screen.queryByRole("link", { name: "Sign in" })).not.toBeInTheDocument();
  });

  it("sends signed-in staff to the dashboard", async () => {
    renderApp(<PublicHeader />, { path: "/careers", user: admin() });

    expect(await screen.findByRole("link", { name: "Dashboard" })).toHaveAttribute("href", "/dashboard");
  });
});
