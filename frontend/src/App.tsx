import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AppLayout } from "./shared/components/AppLayout";
import { RolesPage } from "./pages/Roles/RolesPage";

// Root history / Artifacts / Status have no backend endpoint yet (none of
// Yashasvi's four open backend PRs add one) -- their routes land once
// there's a real shape to build against, not before.
export default function App() {
  return (
    <BrowserRouter>
      <AppLayout>
        <Routes>
          <Route path="/" element={<RolesPage />} />
        </Routes>
      </AppLayout>
    </BrowserRouter>
  );
}
