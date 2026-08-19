import { render, screen, fireEvent } from "@testing-library/react";
import { Pagination } from "../Pagination";

describe("Pagination", () => {
  it("shows the current range and total, and disables Previous on the first page", () => {
    render(<Pagination page={1} pageSize={50} total={64} onPageChange={() => {}} />);

    expect(screen.getByText("Showing 1–50 of 64")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Previous" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Next" })).not.toBeDisabled();
  });

  it("shows the final partial page and disables Next on the last page", () => {
    render(<Pagination page={2} pageSize={50} total={64} onPageChange={() => {}} />);

    expect(screen.getByText("Showing 51–64 of 64")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Next" })).toBeDisabled();
  });

  it("calls onPageChange with the next page", () => {
    const onPageChange = jest.fn();
    render(<Pagination page={1} pageSize={50} total={64} onPageChange={onPageChange} />);

    fireEvent.click(screen.getByRole("button", { name: "Next" }));

    expect(onPageChange).toHaveBeenCalledWith(2);
  });
});
