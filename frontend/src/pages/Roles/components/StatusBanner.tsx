import type { RoleStatus } from "../types/overview.types";

interface StatusBannerProps {
  status: RoleStatus;
  verificationError: string | null;
  checkedAt: string;
}

// Surfaces OverviewResponse.status / .verification_error directly -- per
// the architecture doc's governing rule, a broken trust chain is a normal
// 200 answer and showing it clearly is the point of this page, not an
// edge case to bury in a table row.
export function StatusBanner({ status, verificationError, checkedAt }: StatusBannerProps) {
  if (status === "valid") {
    return (
      <div className="status-banner status-banner--valid">
        Metadata chain verified · checked {checkedAt}
      </div>
    );
  }

  return (
    <div className="status-banner status-banner--broken">
      <strong>Trust chain broken: {status}</strong>
      {verificationError && <p>{verificationError}</p>}
      <p>checked {checkedAt}</p>
    </div>
  );
}
