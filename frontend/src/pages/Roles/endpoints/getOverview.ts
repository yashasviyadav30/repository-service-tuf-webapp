import { httpClient } from "../../../lib/httpClient";
import { simulateLatency } from "../../../lib/mockDelay";
import type { OverviewResponse } from "../types/overview.types";
import { mockOverviewValid } from "./mocks/overviewMock";

const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === "true";

export interface GetOverviewParams {
  // Mirrors the real ?refresh= query param on GET /api/v1/overview --
  // discards the server's 30s cache and checks the repository again.
  refresh?: boolean;
}

// Swap point: once #7 (backend/overview) merges, flip VITE_USE_MOCKS --
// components/hooks never change, they only ever see a
// Promise<OverviewResponse>.
export async function getOverview(
  params: GetOverviewParams = {},
): Promise<OverviewResponse> {
  if (USE_MOCKS) {
    await simulateLatency();
    return mockOverviewValid;
  }
  const query = params.refresh ? "?refresh=true" : "";
  return httpClient.get<OverviewResponse>(`/v1/overview${query}`);
}
