// Mirrors backend/app/dto/schemas.py exactly (PR #23 on the webapp repo,
// commit 36e19e25ee). Field names, casing, and optionality are copied
// verbatim -- nothing here is guessed.
//
// RoleStatus/ExpiryBand come from shared/overview/types instead of being
// redeclared -- they're byte-identical across every PR's schemas.py and
// already the vocabulary TrustPill/ExpiryBadge use.

import type { ExpiryBand, RoleStatus } from "../../../shared/overview/types";

export interface KeySummary {
  keyid: string;
  keyid_short: string;
  name: string;
  scheme: string;
  online: boolean;
  signs: string[];
}

export interface ArtifactSummary {
  path: string;
  length: number;
  hashes: Record<string, string>;
  role: string;
}

export interface RoleDetailResponse {
  name: string;
  version: number;
  expires: string;
  expires_in: string;
  band: ExpiryBand;
  status: RoleStatus;
  threshold: number | null;
  signed_by: KeySummary[];
  signatures_present: number | null;
  signature_note: string | null;
  delegates_to: string[];
  artifacts: ArtifactSummary[];
  raw_url: string;
}
