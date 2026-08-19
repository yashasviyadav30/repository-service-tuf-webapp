import { useEffect, useState } from "react";
import { getRoots } from "../endpoints/getRoots";
import type { RootsResponse } from "../types/roots.types";

interface UseRootsResult {
  data: RootsResponse | null;
  loading: boolean;
  error: string | null;
}

// No refresh param -- like /status and /roles/{role}, /roots has none in
// its schema; only /overview does.
export function useRoots(): UseRootsResult {
  const [data, setData] = useState<RootsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    getRoots()
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
  }, []);

  return { data, loading, error };
}
