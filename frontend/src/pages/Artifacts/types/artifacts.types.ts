// Mirrors backend/app/dto/schemas.py exactly (PR #23 on the webapp repo,
// commit 36e19e25ee -- standardizing on #23's version rather than #22's,
// same call made in the role-detail PR). Field names, casing, and
// optionality are copied verbatim -- nothing here is guessed.
//
// ArtifactBinsResponse/BinSummary aren't declared -- this page only wires
// GET /api/v1/artifacts (search + paging), not the bins endpoint; the UI
// spec has no bin selector, so there's nothing here to build against it.

export interface ArtifactSummary {
  path: string;
  length: number;
  hashes: Record<string, string>;
  role: string;
}

export interface ArtifactsResponse {
  total: number;
  page: number;
  page_size: number;
  artifacts: ArtifactSummary[];
  unavailable: string[];
}
