import { useEffect, useState } from "react";
import { getRole } from "../endpoints/getRole";
import type { RoleDetailResponse } from "../types/role.types";

interface UseRoleResult {
  data: RoleDetailResponse | null;
  loading: boolean;
  error: string | null;
}

// No refresh param -- like /status and /roots, /roles/{role} has none in
// its schema; only /overview does.
export function useRole(role: string | null): UseRoleResult {
  const [data, setData] = useState<RoleDetailResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!role) {
      setData(null);
      setError(null);
      return;
    }
    let cancelled = false;
    setLoading(true);
    getRole(role)
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
  }, [role]);

  return { data, loading, error };
}
