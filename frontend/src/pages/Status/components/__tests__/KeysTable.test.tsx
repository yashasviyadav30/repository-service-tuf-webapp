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
  it("renders one row per key with its signed roles and who holds it", () => {
    render(<KeysTable keys={[key]} />);

    expect(screen.getByText("online_key")).toBeInTheDocument();
    expect(screen.getByText("timestamp, snapshot")).toBeInTheDocument();
    expect(screen.getByText("RSTUF (online)")).toBeInTheDocument();
  });

  it("marks an offline key as held offline, and dashes when it signs nothing", () => {
    render(<KeysTable keys={[{ ...key, name: "", signs: [], online: false }]} />);
    expect(screen.getByText("a1b2c3d4")).toBeInTheDocument();
    expect(screen.getByText("—")).toBeInTheDocument();
    expect(screen.getByText("Offline")).toBeInTheDocument();
  });
});
