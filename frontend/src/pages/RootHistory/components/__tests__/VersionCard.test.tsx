import { render, screen } from "@testing-library/react";
import { VersionCard } from "../VersionCard";
import type { RootVersionSummary } from "../../types/roots.types";

const version: RootVersionSummary = {
  version: 3,
  expires: "2027-08-12T07:40:04+00:00",
  expires_in: "expires 2027-08-12",
  band: "valid",
  superseded: false,
  verified: true,
  by_own_keys: { verified: true, present: 2, threshold: 2 },
  by_previous_keys: { verified: true, present: 1, threshold: 1 },
  note: null,
  key_count: 2,
  keys_changed: [],
  roles_changed: [],
};

describe("VersionCard", () => {
  it("labels the current version as in force", () => {
    render(<VersionCard version={version} supersededBy={null} />);
    expect(screen.getByText(/version 3 -- in force/i)).toBeInTheDocument();
    expect(screen.getByText(/signed by its own keys: 2 of 2 required/i)).toBeInTheDocument();
    expect(screen.getByText(/authorised by version 2: 1 of 1 required/i)).toBeInTheDocument();
  });

  it("labels a superseded version with which version replaced it", () => {
    render(<VersionCard version={{ ...version, superseded: true }} supersededBy={3} />);
    expect(screen.getByText(/version 3 -- superseded by version 3/i)).toBeInTheDocument();
  });

  it("has no predecessor bullet for version one", () => {
    render(<VersionCard version={{ ...version, version: 1, by_previous_keys: null }} supersededBy={2} />);
    expect(screen.queryByText(/authorised by version/i)).not.toBeInTheDocument();
  });

  it("renders added keys with a plus and removed keys struck through", () => {
    render(
      <VersionCard
        version={{
          ...version,
          keys_changed: [
            { keyid: "k1", keyid_short: "k1short", name: "new_key", action: "added" },
            { keyid: "k2", keyid_short: "k2short", name: "old_key", action: "removed" },
          ],
        }}
        supersededBy={null}
      />,
    );

    expect(screen.getByText("+ new_key (k1short)")).toBeInTheDocument();
    expect(screen.getByText("old_key (k2short)").tagName).toBe("S");
  });
});
