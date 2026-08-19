interface PaginationProps {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
}

export function Pagination({ page, pageSize, total, onPageChange }: PaginationProps) {
  const start = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const end = Math.min(page * pageSize, total);
  const hasPrevious = page > 1;
  const hasNext = end < total;

  return (
    <div className="artifacts-pagination">
      <span>{total === 0 ? "No artifacts" : `Showing ${start}–${end} of ${total}`}</span>
      <button type="button" onClick={() => onPageChange(page - 1)} disabled={!hasPrevious}>
        Previous
      </button>
      <button type="button" onClick={() => onPageChange(page + 1)} disabled={!hasNext}>
        Next
      </button>
    </div>
  );
}
