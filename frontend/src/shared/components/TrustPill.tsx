import type { TrustState } from "../overview/trustState";
import { StatusDot } from "./StatusDot";

interface TrustPillProps {
  state: TrustState;
}

const LABEL: Record<TrustState, string> = {
  healthy: "Healthy",
  expiring: "Expires within a day",
  expired: "Expired",
  invalid: "Verification failed",
};

const DOT_COLOR: Record<TrustState, "green" | "amber" | "red"> = {
  healthy: "green",
  expiring: "amber",
  expired: "red",
  invalid: "red",
};

export function TrustPill({ state }: TrustPillProps) {
  return (
    <span className={`trust-pill trust-pill--${state}`}>
      <StatusDot color={DOT_COLOR[state]} />
      {LABEL[state]}
    </span>
  );
}
