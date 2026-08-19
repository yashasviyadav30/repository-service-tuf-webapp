import { fireEvent, render, screen } from "@testing-library/react";
import { DelegationTree } from "../DelegationTree";

const edges = [
  { parent: "root", child: "targets" },
  { parent: "targets", child: "bins-0" },
  { parent: "targets", child: "bins-1" },
];
const delegated = [
  { name: "bins-0", version: 3 },
  { name: "bins-1", version: 2 },
];

describe("DelegationTree", () => {
  it("renders top-level roles with delegated bins collapsed behind a count", () => {
    render(<DelegationTree edges={edges} delegated={delegated} selectedRole={null} onSelectRole={() => {}} />);

    expect(screen.getByText("targets")).toBeInTheDocument();
    expect(screen.getByText("2 delegated roles / click to expand")).toBeInTheDocument();
    expect(screen.queryByText("bins-0")).not.toBeInTheDocument();
  });

  it("expands to show individual bins on click", () => {
    render(<DelegationTree edges={edges} delegated={delegated} selectedRole={null} onSelectRole={() => {}} />);

    fireEvent.click(screen.getByText("2 delegated roles / click to expand"));

    expect(screen.getByText("bins-0 v3")).toBeInTheDocument();
    expect(screen.getByText("bins-1 v2")).toBeInTheDocument();
  });

  it("highlights the selected node and calls back on click", () => {
    const onSelectRole = jest.fn();
    render(<DelegationTree edges={edges} delegated={delegated} selectedRole="targets" onSelectRole={onSelectRole} />);

    expect(screen.getByText("targets")).toHaveClass("tree-node--selected");

    fireEvent.click(screen.getByText("targets"));
    expect(onSelectRole).toHaveBeenCalledWith("targets");
  });
});
