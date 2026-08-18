import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AppLayout } from "./shared/components/AppLayout";
import { RolesPage } from "./pages/Roles/RolesPage";
import { StatusPage } from "./pages/Status/StatusPage";

// Root history / Artifacts have no backend endpoint yet -- their routes
// land once there's a real shape to build against, not before.
export default function App() {
  return (
    <BrowserRouter>
      <AppLayout>
        <Routes>
          <Route path="/" element={<RolesPage />} />
          <Route path="/status" element={<StatusPage />} />
        </Routes>
      </AppLayout>
    </BrowserRouter>
  );
}
