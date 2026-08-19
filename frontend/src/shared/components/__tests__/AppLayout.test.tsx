import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { OverviewProvider } from "../../overview/OverviewContext";
import { AppLayout } from "../AppLayout";

describe("AppLayout", () => {
  it("renders nav links and its children", () => {
    render(
      <MemoryRouter>
        <OverviewProvider>
          <AppLayout>
            <p>content</p>
          </AppLayout>
        </OverviewProvider>
      </MemoryRouter>,
    );

    expect(screen.getByRole("link", { name: "Roles" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Root history" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Artifacts" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Status" })).toBeInTheDocument();
    expect(screen.getByText("content")).toBeInTheDocument();
  });
});
