import type { ReactNode } from "react";
import { Link } from "react-router-dom";

interface AppLayoutProps {
  children: ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  return (
    <div className="app-shell">
      <nav className="app-nav">
        <Link to="/">Overview</Link>
        <Link to="/artifacts">Artifacts</Link>
      </nav>
      <main>{children}</main>
    </div>
  );
}
