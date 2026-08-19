interface SearchBoxProps {
  value: string;
  onChange: (value: string) => void;
}

export function SearchBox({ value, onChange }: SearchBoxProps) {
  return (
    <input
      type="search"
      placeholder="Search by path"
      aria-label="Search artifacts by path"
      value={value}
      onChange={(event) => onChange(event.target.value)}
    />
  );
}
