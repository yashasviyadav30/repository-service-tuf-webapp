import { httpClient } from "../../../lib/httpClient";
import type { RootsResponse } from "../types/roots.types";

// GET /api/v1/roots takes a `limit` query param (1-256, default 20) --
// not exposed here; the page always asks for the server's default window.
export async function getRoots(): Promise<RootsResponse> {
  return httpClient.get<RootsResponse>("/v1/roots");
}
