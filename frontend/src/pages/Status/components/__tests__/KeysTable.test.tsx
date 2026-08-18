import { render, screen } from "@testing-library/react";
import { KeysTable } from "../KeysTable";
import type { KeySummary } from "../../types/status.types";

const key: KeySummary = {
  keyid: "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
  keyid_short: "a1b2c3d4",
  name: "online_key",
  scheme: "ed25519",
  online: true,
  signs: ["timestamp", "snapshot"],
};

describe("KeysTable", () => {
  it("renders one row per key with its scheme, online state, and signed roles", () => {
    render(<KeysTable keys={[key]} />);

    expect(screen.getByText("online_key")).toBeInTheDocument();
    expect(screen.getByText("ed25519")).toBeInTheDocument();
    expect(screen.getByText("Yes")).toBeInTheDocument();
    expect(screen.getByText("timestamp, snapshot")).toBeInTheDocument();
  });

  it("falls back to the short keyid when a key has no name, and dashes when it signs nothing", () => {
    render(<KeysTable keys={[{ ...key, name: "", signs: [] }]} />);
    expect(screen.getByText("a1b2c3d4")).toBeInTheDocument();
    expect(screen.getByText("—")).toBeInTheDocument();
  });
});
