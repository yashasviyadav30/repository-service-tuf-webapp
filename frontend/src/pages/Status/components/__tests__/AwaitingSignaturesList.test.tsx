import { render, screen } from "@testing-library/react";
import { AwaitingSignaturesList } from "../AwaitingSignaturesList";

describe("AwaitingSignaturesList", () => {
  it("lists each role waiting on a signature", () => {
    render(<AwaitingSignaturesList roles={["root"]} />);
    expect(screen.getByText("root")).toBeInTheDocument();
  });

  it("renders nothing when no role is awaiting a signature", () => {
    const { container } = render(<AwaitingSignaturesList roles={[]} />);
    expect(container).toBeEmptyDOMElement();
  });
});
