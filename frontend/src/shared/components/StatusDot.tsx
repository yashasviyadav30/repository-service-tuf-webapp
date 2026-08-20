type StatusDotColor = "green" | "amber" | "red" | "blue" | "purple" | "gray";

interface StatusDotProps {
  color: StatusDotColor;
}

export function StatusDot({ color }: StatusDotProps) {
  return <span className={`status-dot status-dot--${color}`} />;
}
