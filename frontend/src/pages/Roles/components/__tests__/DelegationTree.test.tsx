import { render, screen } from "@testing-library/react";
import { DelegationTree } from "../DelegationTree";

describe("DelegationTree", () => {
  it("renders top-level roles and delegated bins as a nested list", () => {
    render(
      <DelegationTree
        edges={[
          { parent: "root", child: "targets" },
          { parent: "targets", child: "bins-0" },
        ]}
        delegated={[{ name: "bins-0", version: 3 }]}
      />,
    );

    expect(screen.getByText("targets")).toBeInTheDocument();
    expect(screen.getByText("bins-0")).toBeInTheDocument();
    expect(screen.getByText("v3")).toBeInTheDocument();
  });
});
