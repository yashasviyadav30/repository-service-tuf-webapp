import { useMocks } from "../../../lib/env";
import { httpClient } from "../../../lib/httpClient";
import { simulateLatency } from "../../../lib/mockDelay";
import type { StatusResponse } from "../types/status.types";
import { mockStatusReady } from "./mocks/statusMock";

// GET /api/v1/status takes no query params -- unlike overview, there is no
// refresh flag to thread through.
//
// Swap point: once #20 (backend/status) merges, flip VITE_USE_MOCKS --
// components/hooks never change, they only ever see a
// Promise<StatusResponse>.
export async function getStatus(): Promise<StatusResponse> {
  if (useMocks) {
    await simulateLatency();
    return mockStatusReady;
  }
  return httpClient.get<StatusResponse>("/v1/status");
}
