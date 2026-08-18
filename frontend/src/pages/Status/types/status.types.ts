// Mirrors backend/app/dto/schemas.py exactly (PR #20 on the webapp repo,
// backend/status). Field names, casing, and optionality are copied
// verbatim -- nothing here is guessed. Keep this in sync with schemas.py
// as #20 moves through review.

export type RepositoryState =
  | "ready"
  | "not_initialised"
  | "initialising"
  | "awaiting_signatures";

export interface KeySummary {
  keyid: string;
  keyid_short: string;
  name: string;
  scheme: string;
  online: boolean;
  signs: string[];
}

export interface StatusResponse {
  available: boolean; // false when the RSTUF API cannot be reached
  state: RepositoryState;
  bootstrap: string | null;
  awaiting_signatures: string[];
  keys: KeySummary[];
  message: string | null;
}
