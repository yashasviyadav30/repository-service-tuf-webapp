import type { RoleStatus } from "../overview/types";

interface TrustPillProps {
  status: RoleStatus;
}

const LABEL: Record<RoleStatus, string> = {
  valid: "Healthy",
  expired: "Expired",
  invalid: "Verification failed",
};

// Spec also names an "expires within a day" pill state, but nothing in
// OverviewResponse marks that repository-wide -- only a per-role
// ExpiryBand, and CRITICAL there is timestamp's normal daily-renewal
// state, not a warning. Left out rather than guessed at.
export function TrustPill({ status }: TrustPillProps) {
  return <span className={`trust-pill trust-pill--${status}`}>{LABEL[status]}</span>;
}
