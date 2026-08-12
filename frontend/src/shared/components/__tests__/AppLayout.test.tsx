import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { AppLayout } from "../AppLayout";

describe("AppLayout", () => {
  it("renders nav links and its children", () => {
    render(
      <MemoryRouter>
        <AppLayout>
          <p>content</p>
        </AppLayout>
      </MemoryRouter>,
    );

    expect(screen.getByRole("link", { name: "Overview" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Artifacts" })).toBeInTheDocument();
    expect(screen.getByText("content")).toBeInTheDocument();
  });
});
