import { httpClient } from "../../../lib/httpClient";
import type { StatusResponse } from "../types/status.types";

// GET /api/v1/status takes no query params -- unlike overview, there is no
// refresh flag to thread through.
export async function getStatus(): Promise<StatusResponse> {
  return httpClient.get<StatusResponse>("/v1/status");
}
