import { useEffect, useState } from "react";
import { getArtifacts } from "../endpoints/getArtifacts";
import type { ArtifactsResponse } from "../types/artifacts.types";

const PAGE_SIZE = 50;

interface UseArtifactsResult {
  data: ArtifactsResponse | null;
  loading: boolean;
  error: string | null;
  search: string;
  setSearch: (value: string) => void;
  page: number;
  setPage: (value: number) => void;
}

export function useArtifacts(): UseArtifactsResult {
  const [search, setSearchState] = useState("");
  const [page, setPage] = useState(1);
  const [data, setData] = useState<ArtifactsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Any new search starts back at page one -- an old page number would
  // otherwise point at whatever the narrower result set has left there.
  const setSearch = (value: string) => {
    setSearchState(value);
    setPage(1);
  };

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    getArtifacts({ search, page, pageSize: PAGE_SIZE })
      .then((result) => {
        if (!cancelled) setData(result);
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(err instanceof Error ? err.message : "Unknown error");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [search, page]);

  return { data, loading, error, search, setSearch, page, setPage };
}
