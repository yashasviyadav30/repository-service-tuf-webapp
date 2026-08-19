import { useMocks } from "../../../lib/env";
import { httpClient } from "../../../lib/httpClient";
import { simulateLatency } from "../../../lib/mockDelay";
import type { RoleDetailResponse } from "../types/role.types";
import { mockRoleDetail } from "./mocks/roleMock";

// Swap point: once #23 (backend/role-detail) merges, flip VITE_USE_MOCKS --
// components/hooks never change, they only ever see a
// Promise<RoleDetailResponse>.
export async function getRole(role: string): Promise<RoleDetailResponse> {
  if (useMocks) {
    await simulateLatency();
    return { ...mockRoleDetail, name: role, raw_url: `/api/v1/roles/${role}/raw` };
  }
  return httpClient.get<RoleDetailResponse>(`/v1/roles/${encodeURIComponent(role)}`);
}
