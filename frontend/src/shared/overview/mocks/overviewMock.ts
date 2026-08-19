import type { OverviewResponse } from "../types";

// Shaped to match GET /api/v1/overview once #7 merges -- fields and
// nesting copied from schemas.py, not invented. Used by vite.mockApi.ts
// (dev server) and by tests that mock getOverview -- application code
// never imports this directly.
export const mockOverviewValid: OverviewResponse = {
  status: "valid",
  checked_at: "2026-08-15T09:41:08+00:00",
  roles: [
    {
      name: "root",
      version: 3,
      expires: "2027-08-12T07:40:04+00:00",
      expires_in: "expires 2027-08-12",
      band: "valid",
      threshold: 2,
      key_count: 2,
      key_names: ["root_key_1", "root_key_2"],
      status: "valid",
    },
    {
      name: "timestamp",
      version: 118,
      expires: "2026-08-16T09:00:00+00:00",
      expires_in: "expires in about 18 hours",
      band: "critical",
      threshold: 1,
      key_count: 1,
      key_names: ["online_key"],
      status: "valid",
    },
    {
      name: "snapshot",
      version: 42,
      expires: "2026-08-22T09:00:00+00:00",
      expires_in: "expires 2026-08-22",
      band: "expiring",
      threshold: 1,
      key_count: 1,
      key_names: ["online_key"],
      status: "valid",
    },
    {
      name: "targets",
      version: 7,
      expires: "2026-09-14T09:00:00+00:00",
      expires_in: "expires 2026-09-14",
      band: "valid",
      threshold: 1,
      key_count: 1,
      key_names: ["online_key"],
      status: "valid",
    },
  ],
  delegated: [
    { name: "bins-0", version: 3 },
    { name: "bins-1", version: 3 },
    { name: "bins-2", version: 2 },
  ],
  edges: [
    { parent: "root", child: "timestamp" },
    { parent: "root", child: "snapshot" },
    { parent: "root", child: "targets" },
    { parent: "targets", child: "bins-0" },
    { parent: "targets", child: "bins-1" },
    { parent: "targets", child: "bins-2" },
  ],
  verification_error: null,
};

// Broken-trust case -- exercises the status banner without touching a
// real repository. Matches how #7's handler answers when timestamp has
// lapsed: still a 200, status carries the news.
export const mockOverviewExpired: OverviewResponse = {
  status: "expired",
  checked_at: "2026-08-15T09:41:08+00:00",
  roles: [
    {
      name: "root",
      version: 3,
      expires: "2027-08-12T07:40:04+00:00",
      expires_in: "expires 2027-08-12",
      band: "valid",
      threshold: 2,
      key_count: 2,
      key_names: ["root_key_1", "root_key_2"],
      status: "valid",
    },
    {
      name: "timestamp",
      version: 118,
      expires: "2026-08-14T09:00:00+00:00",
      expires_in: "expired 2026-08-14",
      band: "expired",
      threshold: 1,
      key_count: 1,
      key_names: ["online_key"],
      status: "expired",
    },
  ],
  delegated: [],
  edges: [{ parent: "root", child: "timestamp" }],
  verification_error: "timestamp expired at 2026-08-14T09:00:00+00:00",
};
