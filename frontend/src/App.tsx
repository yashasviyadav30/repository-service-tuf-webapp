import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AppLayout } from "./shared/components/AppLayout";

// Page routes land in their own follow-up PRs (frontend/overview-page,
// frontend/artifacts-page) so this scaffold builds and tests standalone.
export default function App() {
  return (
    <BrowserRouter>
      <AppLayout>
        <Routes>
          <Route path="/" element={<p>Pages land in follow-up PRs.</p>} />
        </Routes>
      </AppLayout>
    </BrowserRouter>
  );
}
