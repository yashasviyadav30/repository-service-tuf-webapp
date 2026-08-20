import type { OverviewResponse } from "./types";

export type TrustState = "healthy" | "expiring" | "expired" | "invalid";

const HOURS_WINDOW = 24;

function hoursUntil(iso: string): number {
  return (new Date(iso).getTime() - Date.now()) / (1000 * 60 * 60);
}

// "Expires within a day" has no field of its own in OverviewResponse --
// derived from whether any role's raw `expires` timestamp (otherwise
// unused by the UI; every other display uses the pre-formatted
// expires_in) falls inside the next 24 hours.
export function deriveTrustState(overview: OverviewResponse): TrustState {
  if (overview.status === "invalid") return "invalid";
  if (overview.status === "expired") return "expired";
  const expiringSoon = overview.roles.some((role) => {
    const hours = hoursUntil(role.expires);
    return hours > 0 && hours <= HOURS_WINDOW;
  });
  return expiringSoon ? "expiring" : "healthy";
}
