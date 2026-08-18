import type { RepositoryState } from "../types/status.types";

interface RepositoryStateBannerProps {
  available: boolean;
  state: RepositoryState;
  message: string | null;
}

const STATE_LABEL: Record<RepositoryState, string> = {
  ready: "Repository ready",
  not_initialised: "Repository not initialised",
  initialising: "Repository initialising",
  awaiting_signatures: "Awaiting signatures",
};

// This never fails the request, per the handler's own docstring -- status
// is helpful, not load-bearing. An unreachable RSTUF API renders as its
// own banner state, not as an error thrown up to the page.
export function RepositoryStateBanner({ available, state, message }: RepositoryStateBannerProps) {
  if (!available) {
    return (
      <div className="status-banner status-banner--unavailable">
        <strong>RSTUF API unavailable</strong>
        {message && <p>{message}</p>}
      </div>
    );
  }

  if (state === "ready") {
    return <div className="status-banner status-banner--valid">{STATE_LABEL[state]}</div>;
  }

  return (
    <div className={`status-banner status-banner--${state}`}>
      <strong>{STATE_LABEL[state]}</strong>
      {message && <p>{message}</p>}
    </div>
  );
}
