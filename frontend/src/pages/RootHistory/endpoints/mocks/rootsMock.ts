import type { RootsResponse } from "../../types/roots.types";

// Shaped to match GET /api/v1/roots once #21 merges -- fields and nesting
// copied from schemas.py, not invented. Covers all three shapes a version
// can take: current (band present), superseded (band absent, has a key
// and threshold change), and version one (no by_previous_keys). Used by
// vite.mockApi.ts (dev server) -- application code never imports this
// directly.
export const mockRoots: RootsResponse = {
  current: 3,
  earliest: 1,
  versions: [
    {
      version: 3,
      expires: "2027-08-12T07:40:04+00:00",
      expires_in: "expires 2027-08-12",
      band: "valid",
      superseded: false,
      verified: true,
      by_own_keys: { verified: true, present: 2, threshold: 2 },
      by_previous_keys: { verified: true, present: 1, threshold: 1 },
      note: null,
      key_count: 2,
      keys_changed: [
        {
          keyid: "b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3",
          keyid_short: "b2c3d4e5",
          name: "root_key_2",
          action: "added",
        },
      ],
      roles_changed: [
        {
          role: "root",
          threshold_before: 1,
          threshold_after: 2,
          signers_added: ["root_key_2"],
          signers_removed: [],
        },
      ],
    },
    {
      version: 2,
      expires: "2026-06-01T00:00:00+00:00",
      expires_in: "",
      band: null,
      superseded: true,
      verified: true,
      by_own_keys: { verified: true, present: 1, threshold: 1 },
      by_previous_keys: { verified: true, present: 1, threshold: 1 },
      note: null,
      key_count: 1,
      keys_changed: [
        {
          keyid: "c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4",
          keyid_short: "c3d4e5f6",
          name: "online_key_old",
          action: "removed",
        },
      ],
      roles_changed: [
        {
          role: "timestamp",
          threshold_before: 1,
          threshold_after: 1,
          signers_added: ["online_key"],
          signers_removed: ["online_key_old"],
        },
      ],
    },
    {
      version: 1,
      expires: "2025-01-14T00:00:00+00:00",
      expires_in: "",
      band: null,
      superseded: true,
      verified: true,
      by_own_keys: { verified: true, present: 1, threshold: 1 },
      by_previous_keys: null,
      note: null,
      key_count: 1,
      keys_changed: [],
      roles_changed: [],
    },
  ],
  message: null,
};
