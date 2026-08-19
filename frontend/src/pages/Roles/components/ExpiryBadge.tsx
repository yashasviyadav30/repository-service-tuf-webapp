import type { ExpiryBand } from "../../../shared/overview/types";

interface ExpiryBadgeProps {
  band: ExpiryBand;
  label: string;
}

// className scheme intentionally matches the "block--modifier" pattern
// used elsewhere (e.g. status-card--valid in an earlier page) -- no CSS
// exists to back any of this yet, that's a separate, still-open item.
export function ExpiryBadge({ band, label }: ExpiryBadgeProps) {
  return <span className={`expiry-badge expiry-badge--${band}`}>{label}</span>;
}
