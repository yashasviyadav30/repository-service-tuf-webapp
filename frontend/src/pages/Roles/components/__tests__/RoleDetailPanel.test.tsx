import { render, screen } from "@testing-library/react";
import { RoleDetailPanel } from "../RoleDetailPanel";

describe("RoleDetailPanel", () => {
  it("prompts for a selection", () => {
    render(<RoleDetailPanel />);
    expect(screen.getByText(/select a role/i)).toBeInTheDocument();
  });
});
