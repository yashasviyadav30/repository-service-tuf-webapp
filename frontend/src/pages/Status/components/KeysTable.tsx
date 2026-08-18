import type { KeySummary } from "../types/status.types";

interface KeysTableProps {
  keys: KeySummary[];
}

export function KeysTable({ keys }: KeysTableProps) {
  return (
    <table className="keys-table">
      <thead>
        <tr>
          <th>Key</th>
          <th>Scheme</th>
          <th>Online</th>
          <th>Signs</th>
        </tr>
      </thead>
      <tbody>
        {keys.map((key) => (
          <tr key={key.keyid}>
            <td>{key.name || key.keyid_short}</td>
            <td>{key.scheme || "—"}</td>
            <td>{key.online ? "Yes" : "No"}</td>
            <td>{key.signs.join(", ") || "—"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
