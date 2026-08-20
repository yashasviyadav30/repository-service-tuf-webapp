import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";
import { useOverviewContext } from "../overview/OverviewContext";
import { deriveTrustState } from "../overview/trustState";
import { formatCheckedAt } from "../../lib/formatTime";
import { TrustPill } from "./TrustPill";
import { ErrorBanner } from "./ErrorBanner";
import { Footer } from "./Footer";

interface AppLayoutProps {
  children: ReactNode;
}

const navClassName = ({ isActive }: { isActive: boolean }) => (isActive ? "active" : undefined);

export function AppLayout({ children }: AppLayoutProps) {
  const { data, loading, refresh } = useOverviewContext();

  return (
    <div className="app-shell">
      <header className="app-header">
        <h1>RSTUF Metadata Visualizer</h1>
        {data && <TrustPill state={deriveTrustState(data)} />}
        <div className="app-header__spacer" />
        {data && <span className="last-checked">checked {formatCheckedAt(data.checked_at)}</span>}
        <button className="refresh-button" onClick={refresh} disabled={loading}>
          Refresh
        </button>
      </header>
      <nav className="app-nav">
        <NavLink to="/" end className={navClassName}>
          Roles
        </NavLink>
        <NavLink to="/root-history" className={navClassName}>
          Root history
        </NavLink>
        <NavLink to="/artifacts" className={navClassName}>
          Artifacts
        </NavLink>
        <NavLink to="/status" className={navClassName}>
          Status
        </NavLink>
      </nav>
      {data?.verification_error && <ErrorBanner message={data.verification_error} />}
      <main>{children}</main>
      <Footer />
    </div>
  );
}
