import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { SkillChips } from "./skill-chips";

describe("SkillChips", () => {
  it("shows every skill when there is no limit", () => {
    render(<SkillChips skills={["a", "b", "c"]} />);
    expect(screen.getAllByRole("listitem")).toHaveLength(3);
  });

  it("collapses the overflow into a +N pill", () => {
    render(<SkillChips skills={["a", "b", "c", "d", "e"]} max={3} />);
    expect(screen.getByText("c")).toBeInTheDocument();
    expect(screen.queryByText("d")).not.toBeInTheDocument();
    expect(screen.getByText("+2")).toBeInTheDocument();
  });

  it("renders nothing for an empty list", () => {
    const { container } = render(<SkillChips skills={[]} />);
    expect(container).toBeEmptyDOMElement();
  });
});
