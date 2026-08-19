import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";
import { useOverviewContext } from "../overview/OverviewContext";
import { TrustPill } from "./TrustPill";
import { ErrorBanner } from "./ErrorBanner";
import { Footer } from "./Footer";

interface AppLayoutProps {
  children: ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  const { data, loading, refresh } = useOverviewContext();

  return (
    <div className="app-shell">
      <header className="app-header">
        <h1>RSTUF Metadata Visualizer</h1>
        {data && (
          <>
            <TrustPill status={data.status} />
            <span className="last-checked">checked {data.checked_at}</span>
          </>
        )}
        <button onClick={refresh} disabled={loading}>
          Refresh
        </button>
      </header>
      <nav className="app-nav">
        <NavLink to="/" end>
          Roles
        </NavLink>
        <NavLink to="/root-history">Root history</NavLink>
        <NavLink to="/artifacts">Artifacts</NavLink>
        <NavLink to="/status">Status</NavLink>
      </nav>
      {data?.verification_error && <ErrorBanner message={data.verification_error} />}
      <main>{children}</main>
      <Footer />
    </div>
  );
}
