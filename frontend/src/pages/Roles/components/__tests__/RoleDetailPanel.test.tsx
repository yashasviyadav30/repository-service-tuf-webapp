import { render, screen } from "@testing-library/react";
import { RoleDetailPanel } from "../RoleDetailPanel";

describe("RoleDetailPanel", () => {
  it("prompts for a selection when nothing is selected", () => {
    render(<RoleDetailPanel selectedRole={null} />);
    expect(screen.getByText(/select a role/i)).toBeInTheDocument();
  });

  it("shows a role's details, signatures, delegates, and a raw-file link once loaded", async () => {
    render(<RoleDetailPanel selectedRole="root" />);

    expect(await screen.findByRole("heading", { name: "root" })).toBeInTheDocument();
    expect(screen.getByText("2 of 2")).toBeInTheDocument();
    expect(screen.getByText("root_key_1, root_key_2")).toBeInTheDocument();
    expect(screen.getByText("timestamp, snapshot, targets")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /view signed file/i })).toHaveAttribute(
      "href",
      "/api/v1/roles/root/raw",
    );
  });
});
