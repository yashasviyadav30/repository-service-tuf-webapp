// Mirrors backend/app/dto/schemas.py exactly (PR #6 on the webapp repo,
// commit c5eb414). Field names, casing, and optionality are copied
// verbatim -- nothing here is guessed. Keep this in sync with schemas.py
// as PR #7 (the /overview endpoint itself) moves through review.

export type RoleStatus = "valid" | "expired" | "invalid";

// Four bands, not two -- RSTUF renews timestamp roughly daily, so it sits
// in "critical" whenever the repository is healthy. Collapsing that into
// plain "valid" would throw away the only useful warning.
export type ExpiryBand = "expired" | "critical" | "expiring" | "valid";

export interface RoleSummary {
  name: string;
  version: number;
  expires: string; // ISO-8601
  expires_in: string; // pre-formatted phrase, e.g. "expires 2027-08-12"
  band: ExpiryBand;
  threshold: number | null; // only root declares this
  key_count: number | null;
  key_names: string[];
  status: RoleStatus;
}

export interface DelegatedSummary {
  name: string;
  version: number | null;
}

export interface TreeEdge {
  parent: string;
  child: string;
}

export interface OverviewResponse {
  status: RoleStatus;
  checked_at: string; // stamped when the repository was read, not when served
  roles: RoleSummary[];
  delegated: DelegatedSummary[];
  edges: TreeEdge[];
  verification_error: string | null;
}
