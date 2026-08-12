import type { ReactNode } from "react";
import { Link } from "react-router-dom";

interface AppLayoutProps {
  children: ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  return (
    <div className="app-shell">
      <nav className="app-nav">
        <Link to="/">Roles</Link>
        <Link to="/root-history">Root history</Link>
        <Link to="/artifacts">Artifacts</Link>
        <Link to="/status">Status</Link>
      </nav>
      <main>{children}</main>
    </div>
  );
}
