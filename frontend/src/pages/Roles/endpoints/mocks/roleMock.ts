import type { RoleDetailResponse } from "../../types/role.types";

// Shaped to match GET /api/v1/roles/{role} once #23 merges -- fields and
// nesting copied from schemas.py, not invented. getRole overrides name and
// raw_url to match whichever role was clicked; the rest stays static.
export const mockRoleDetail: RoleDetailResponse = {
  name: "root",
  version: 3,
  expires: "2027-08-12T07:40:04+00:00",
  expires_in: "expires 2027-08-12",
  band: "valid",
  status: "valid",
  threshold: 2,
  signed_by: [
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
      name: "root_key_2",
      scheme: "ed25519",
      online: false,
      signs: ["root"],
    },
  ],
  signatures_present: 2,
  signature_note: null,
  delegates_to: ["timestamp", "snapshot", "targets"],
  artifacts: [],
  raw_url: "/api/v1/roles/root/raw",
};
