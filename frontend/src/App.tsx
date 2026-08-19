import { BrowserRouter, Routes, Route } from "react-router-dom";
import { OverviewProvider } from "./shared/overview/OverviewContext";
import { AppLayout } from "./shared/components/AppLayout";
import { RolesPage } from "./pages/Roles/RolesPage";
import { StatusPage } from "./pages/Status/StatusPage";
import { RootHistoryPage } from "./pages/RootHistory/RootHistoryPage";

// Artifacts has no backend endpoint yet -- its route lands once there's a
// real shape to build against, not before.
export default function App() {
  return (
    <BrowserRouter>
      <OverviewProvider>
        <AppLayout>
          <Routes>
            <Route path="/" element={<RolesPage />} />
            <Route path="/status" element={<StatusPage />} />
            <Route path="/root-history" element={<RootHistoryPage />} />
          </Routes>
        </AppLayout>
      </OverviewProvider>
    </BrowserRouter>
  );
}
