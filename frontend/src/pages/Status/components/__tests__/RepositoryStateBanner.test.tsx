import { render, screen } from "@testing-library/react";
import { RepositoryStateBanner } from "../RepositoryStateBanner";

describe("RepositoryStateBanner", () => {
  it("shows a ready message when the repository is available and ready", () => {
    render(<RepositoryStateBanner available={true} state="ready" message={null} />);
    expect(screen.getByText(/repository ready/i)).toBeInTheDocument();
  });

  it("surfaces the message when awaiting signatures", () => {
    render(
      <RepositoryStateBanner
        available={true}
        state="awaiting_signatures"
        message="Waiting on 1 more signature for root"
      />,
    );
    expect(screen.getByText(/awaiting signatures/i)).toBeInTheDocument();
    expect(screen.getByText(/waiting on 1 more signature/i)).toBeInTheDocument();
  });

  it("renders the unavailable banner when the RSTUF API cannot be reached, regardless of state", () => {
    render(<RepositoryStateBanner available={false} state="ready" message="The RSTUF API did not respond" />);
    expect(screen.getByText(/rstuf api unavailable/i)).toBeInTheDocument();
    expect(screen.getByText(/did not respond/i)).toBeInTheDocument();
  });
});
