import { render, screen } from "@testing-library/react";
import { ExpiryBadge } from "../ExpiryBadge";

describe("ExpiryBadge", () => {
  it("renders the label text with a band-specific className", () => {
    render(<ExpiryBadge band="critical" label="expires in about 18 hours" />);
    const badge = screen.getByText("expires in about 18 hours");
    expect(badge).toHaveClass("expiry-badge--critical");
  });
});
