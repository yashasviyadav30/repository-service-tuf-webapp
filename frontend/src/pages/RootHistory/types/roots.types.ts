// Mirrors backend/app/dto/schemas.py exactly (PR #21 on the webapp repo,
// commit 0e1c26d354). Field names, casing, and optionality are copied
// verbatim -- nothing here is guessed. ExpiryBand is imported from
// shared/overview/types rather than redeclared, same as role.types.ts.

import type { ExpiryBand } from "../../../shared/overview/types";

export type KeyChangeAction = "added" | "removed";

export interface SignatureCheckSummary {
  verified: boolean;
  present: number;
  threshold: number;
}

export interface RootKeyChange {
  keyid: string;
  keyid_short: string;
  name: string;
  action: KeyChangeAction;
}

export interface RootRoleChange {
  role: string;
  threshold_before: number | null;
  threshold_after: number | null;
  signers_added: string[];
  signers_removed: string[];
}

export interface RootVersionSummary {
  version: number;
  expires: string;
  expires_in: string;
  band: ExpiryBand | null; // absent once a version has been superseded
  superseded: boolean;
  verified: boolean;
  by_own_keys: SignatureCheckSummary;
  by_previous_keys: SignatureCheckSummary | null; // absent for version one
  note: string | null;
  key_count: number;
  keys_changed: RootKeyChange[];
  roles_changed: RootRoleChange[];
}

export interface RootsResponse {
  current: number;
  earliest: number;
  versions: RootVersionSummary[];
  message: string | null;
}
