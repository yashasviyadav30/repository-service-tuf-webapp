import type { ArtifactSummary } from "../../types/artifacts.types";

// Shaped to match GET /api/v1/artifacts once #23 merges -- fields copied
// from schemas.py, not invented. 64 rows, generated rather than
// hand-written, so search and paging have something real to work against
// (matches the UI spec's own example: "showing 1-50 of 64"). Used by
// vite.mockApi.ts, which also does the search/paging filtering -- that
// logic belongs in the dev-only mock server, not in application code.
const BINS = ["bins-0", "bins-1", "bins-2"];

function fakeHash(seed: number): string {
  return seed.toString(16).padStart(8, "0").repeat(8).slice(0, 64);
}

export const mockAllArtifacts: ArtifactSummary[] = Array.from({ length: 64 }, (_, i) => ({
  path: `packages/example-pkg-${i}.tar.gz`,
  length: 1024 * (100 + i * 37),
  hashes: { sha256: fakeHash(i) },
  role: BINS[i % BINS.length],
}));
