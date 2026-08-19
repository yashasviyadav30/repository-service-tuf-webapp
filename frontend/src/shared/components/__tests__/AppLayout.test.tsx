import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { OverviewProvider } from "../../overview/OverviewContext";
import { AppLayout } from "../AppLayout";

// getOverview always calls the real API now -- mock it here rather than
// let the test hit a real network call.
jest.mock("../../overview/getOverview", () => ({
  getOverview: jest.fn().mockResolvedValue({
    status: "valid",
    checked_at: "2026-08-15T09:41:08+00:00",
    roles: [],
    delegated: [],
    edges: [],
    verification_error: null,
  }),
}));

describe("AppLayout", () => {
  it("renders nav links and its children", async () => {
    render(
      <MemoryRouter>
        <OverviewProvider>
          <AppLayout>
            <p>content</p>
          </AppLayout>
        </OverviewProvider>
      </MemoryRouter>,
    );

    // Waits for the mocked getOverview() to resolve before asserting, so
    // the state update it triggers doesn't land after the test returns.
    expect(await screen.findByRole("link", { name: "Roles" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Root history" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Artifacts" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Status" })).toBeInTheDocument();
    expect(screen.getByText("content")).toBeInTheDocument();
  });
});
