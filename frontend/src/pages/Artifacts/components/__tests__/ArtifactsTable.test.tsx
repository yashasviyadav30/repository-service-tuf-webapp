import { render, screen } from "@testing-library/react";
import { ArtifactsTable } from "../ArtifactsTable";
import type { ArtifactSummary } from "../../types/artifacts.types";

const artifact: ArtifactSummary = {
  path: "packages/example.tar.gz",
  length: 2048,
  hashes: { sha256: "abcdef0123456789abcdef0123456789abcdef0123456789abcdef01234567" },
  role: "bins-0",
};

describe("ArtifactsTable", () => {
  it("renders path, role, a human-readable size, and a truncated hash", () => {
    render(<ArtifactsTable artifacts={[artifact]} />);

    expect(screen.getByText("packages/example.tar.gz")).toBeInTheDocument();
    expect(screen.getByText("bins-0")).toBeInTheDocument();
    expect(screen.getByText("2.0 KB")).toBeInTheDocument();
    expect(screen.getByText("abcdef012345")).toBeInTheDocument();
  });

  it("shows a dash when a hash has no sha256 entry", () => {
    render(<ArtifactsTable artifacts={[{ ...artifact, hashes: {} }]} />);
    expect(screen.getByText("—")).toBeInTheDocument();
  });
});
