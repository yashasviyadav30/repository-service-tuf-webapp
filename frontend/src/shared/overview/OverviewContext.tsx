import { createContext, useContext, type ReactNode } from "react";
import { useOverview } from "./useOverview";
import type { OverviewResponse } from "./types";

interface OverviewContextValue {
  data: OverviewResponse | null;
  loading: boolean;
  error: string | null;
  refresh: () => void;
}

const OverviewContext = createContext<OverviewContextValue | null>(null);

// One shared fetch -- the shell (status pill, last-checked, error banner)
// and the Roles page (table, tree) both read GET /api/v1/overview, and a
// second independent fetch would desync instead of duplicating work.
export function OverviewProvider({ children }: { children: ReactNode }) {
  const value = useOverview();
  return <OverviewContext.Provider value={value}>{children}</OverviewContext.Provider>;
}

export function useOverviewContext(): OverviewContextValue {
  const value = useContext(OverviewContext);
  if (!value) {
    throw new Error("useOverviewContext must be used within OverviewProvider");
  }
  return value;
}
