import { render, screen } from "@testing-library/react";
import { StatusBanner } from "../StatusBanner";

describe("StatusBanner", () => {
  it("shows a verified message when status is valid", () => {
    render(<StatusBanner status="valid" verificationError={null} checkedAt="2026-08-15T09:41:08+00:00" />);
    expect(screen.getByText(/verified/i)).toBeInTheDocument();
  });

  it("surfaces the verification error when the trust chain is broken", () => {
    render(
      <StatusBanner
        status="expired"
        verificationError="timestamp expired at 2026-08-14T09:00:00+00:00"
        checkedAt="2026-08-15T09:41:08+00:00"
      />,
    );
    expect(screen.getByText(/trust chain broken: expired/i)).toBeInTheDocument();
    expect(screen.getByText(/timestamp expired at/)).toBeInTheDocument();
  });
});
