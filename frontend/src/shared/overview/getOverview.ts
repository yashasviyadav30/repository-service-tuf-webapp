import { httpClient } from "../../lib/httpClient";
import type { OverviewResponse } from "./types";

export interface GetOverviewParams {
  // Mirrors the real ?refresh= query param on GET /api/v1/overview --
  // discards the server's 30s cache and checks the repository again.
  refresh?: boolean;
}

export async function getOverview(
  params: GetOverviewParams = {},
): Promise<OverviewResponse> {
  const query = params.refresh ? "?refresh=true" : "";
  return httpClient.get<OverviewResponse>(`/v1/overview${query}`);
}
