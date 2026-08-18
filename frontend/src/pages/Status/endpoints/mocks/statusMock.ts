import type { StatusResponse } from "../../types/status.types";

// Shaped to match GET /api/v1/status once #20 merges -- fields and nesting
// copied from schemas.py, not invented. Delete this file's export (or flip
// VITE_USE_MOCKS) once that endpoint is live; components/hooks don't
// change either way.
export const mockStatusReady: StatusResponse = {
  available: true,
  state: "ready",
  bootstrap: "2026-01-14T10:00:00+00:00",
  awaiting_signatures: [],
  keys: [
    {
      keyid: "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
      keyid_short: "a1b2c3d4",
      name: "root_key_1",
      scheme: "ed25519",
      online: false,
      signs: ["root"],
    },
    {
      keyid: "f6e5d4c3b2a1f6e5d4c3b2a1f6e5d4c3b2a1f6e5d4c3b2a1f6e5d4c3b2a1f6e5",
      keyid_short: "f6e5d4c3",
      name: "online_key",
      scheme: "ed25519",
      online: true,
      signs: ["timestamp", "snapshot", "targets"],
    },
  ],
  message: null,
};

// Awaiting-signatures case -- exercises the banner's non-ready branch and
// the awaiting-signatures list without touching a real repository. Matches
// how #20's handler answers mid-rotation, before every required signer has
// countersigned root.
export const mockStatusAwaitingSignatures: StatusResponse = {
  available: true,
  state: "awaiting_signatures",
  bootstrap: "2026-01-14T10:00:00+00:00",
  awaiting_signatures: ["root"],
  keys: [
    {
      keyid: "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
      keyid_short: "a1b2c3d4",
      name: "root_key_1",
      scheme: "ed25519",
      online: false,
      signs: ["root"],
    },
  ],
  message: "Waiting on 1 more signature for root",
};

// Unreachable case -- this is the one RSTUF-side failure that never fails
// the request (per #20's handler docstring): available is false, every
// other field falls back to its default, and message carries the reason.
export const mockStatusUnavailable: StatusResponse = {
  available: false,
  state: "not_initialised",
  bootstrap: null,
  awaiting_signatures: [],
  keys: [],
  message: "The RSTUF API did not respond",
};
