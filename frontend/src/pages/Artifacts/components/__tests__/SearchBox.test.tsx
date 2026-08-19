import { render, screen, fireEvent } from "@testing-library/react";
import { SearchBox } from "../SearchBox";

describe("SearchBox", () => {
  it("calls onChange as the user types", () => {
    const onChange = jest.fn();
    render(<SearchBox value="" onChange={onChange} />);

    fireEvent.change(screen.getByRole("searchbox"), { target: { value: "example" } });

    expect(onChange).toHaveBeenCalledWith("example");
  });
});
