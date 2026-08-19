import { render, screen } from "@testing-library/react";
import { VersionTimeline } from "../VersionTimeline";
import type { RootVersionSummary } from "../../types/roots.types";

const base: Omit<RootVersionSummary, "version" | "superseded"> = {
  expires: "2027-08-12T07:40:04+00:00",
  expires_in: "expires 2027-08-12",
  band: "valid",
  verified: true,
  by_own_keys: { verified: true, present: 1, threshold: 1 },
  by_previous_keys: null,
  note: null,
  key_count: 1,
  keys_changed: [],
  roles_changed: [],
};

describe("VersionTimeline", () => {
  it("derives each superseded version's replacement from list position, newest first", () => {
    render(
      <VersionTimeline
        versions={[
          { ...base, version: 2, superseded: false },
          { ...base, version: 1, superseded: true },
        ]}
      />,
    );

    expect(screen.getByText(/version 2 -- in force/i)).toBeInTheDocument();
    expect(screen.getByText(/version 1 -- superseded by version 2/i)).toBeInTheDocument();
  });
});
