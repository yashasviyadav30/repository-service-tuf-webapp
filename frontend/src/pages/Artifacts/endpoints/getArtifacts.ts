import { httpClient } from "../../../lib/httpClient";
import type { ArtifactsResponse } from "../types/artifacts.types";

export interface GetArtifactsParams {
  search?: string;
  role?: string;
  page?: number;
  pageSize?: number;
}

export async function getArtifacts(params: GetArtifactsParams = {}): Promise<ArtifactsResponse> {
  const query = new URLSearchParams();
  if (params.search) query.set("search", params.search);
  if (params.role) query.set("role", params.role);
  if (params.page) query.set("page", String(params.page));
  if (params.pageSize) query.set("page_size", String(params.pageSize));

  const qs = query.toString();
  return httpClient.get<ArtifactsResponse>(`/v1/artifacts${qs ? `?${qs}` : ""}`);
}
