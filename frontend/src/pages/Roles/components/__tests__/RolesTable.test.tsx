import { render, screen } from "@testing-library/react";
import { RolesTable } from "../RolesTable";
import type { RoleSummary } from "../../../../shared/overview/types";

const role: RoleSummary = {
  name: "root",
  version: 3,
  expires: "2027-08-12T07:40:04+00:00",
  expires_in: "expires 2027-08-12",
  band: "valid",
  threshold: 2,
  key_count: 2,
  key_names: ["root_key_1", "root_key_2"],
  status: "valid",
};

describe("RolesTable", () => {
  it("renders one row per role with its version, expiry, threshold, and signers", () => {
    render(<RolesTable roles={[role]} />);

    expect(screen.getByText("root")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getByText("expires 2027-08-12")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.getByText("root_key_1, root_key_2")).toBeInTheDocument();
  });

  it("renders a dash for a role with no declared threshold", () => {
    render(<RolesTable roles={[{ ...role, threshold: null, key_names: [] }]} />);
    expect(screen.getAllByText("—")).toHaveLength(2);
  });
});
