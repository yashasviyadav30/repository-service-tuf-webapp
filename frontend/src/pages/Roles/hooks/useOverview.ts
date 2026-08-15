import { useCallback, useEffect, useState } from "react";
import { getOverview } from "../endpoints/getOverview";
import type { OverviewResponse } from "../types/overview.types";

interface UseOverviewResult {
  data: OverviewResponse | null;
  loading: boolean;
  error: string | null;
  refresh: () => void;
}

export function useOverview(): UseOverviewResult {
  const [data, setData] = useState<OverviewResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // Bumping this re-runs the effect below with refresh:true -- keeps the
  // fetch logic in one place instead of duplicating it in a click handler.
  const [refreshToken, setRefreshToken] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    getOverview({ refresh: refreshToken > 0 })
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
  }, [refreshToken]);

  const refresh = useCallback(() => setRefreshToken((token) => token + 1), []);

  return { data, loading, error, refresh };
}
