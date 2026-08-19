import { render, screen } from "@testing-library/react";
import { RoleChangeTable } from "../RoleChangeTable";

describe("RoleChangeTable", () => {
  it("renders a threshold transition and the added/removed signers", () => {
    render(
      <RoleChangeTable
        changes={[
          { role: "root", threshold_before: 1, threshold_after: 2, signers_added: ["root_key_2"], signers_removed: [] },
        ]}
      />,
    );

    expect(screen.getByText("root")).toBeInTheDocument();
    expect(screen.getByText("1 → 2")).toBeInTheDocument();
    expect(screen.getByText("+root_key_2")).toBeInTheDocument();
  });

  it("shows a dash when neither signers nor threshold changed", () => {
    render(
      <RoleChangeTable
        changes={[
          { role: "timestamp", threshold_before: 1, threshold_after: 1, signers_added: [], signers_removed: [] },
        ]}
      />,
    );

    expect(screen.getByText("1")).toBeInTheDocument();
    expect(screen.getByText("—")).toBeInTheDocument();
  });
});
