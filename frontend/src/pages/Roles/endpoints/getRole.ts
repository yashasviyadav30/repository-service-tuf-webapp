import { httpClient } from "../../../lib/httpClient";
import type { RoleDetailResponse } from "../types/role.types";

export async function getRole(role: string): Promise<RoleDetailResponse> {
  return httpClient.get<RoleDetailResponse>(`/v1/roles/${encodeURIComponent(role)}`);
}
