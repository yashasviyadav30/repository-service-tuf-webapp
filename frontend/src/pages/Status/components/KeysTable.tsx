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
          <th>Signs</th>
          <th>Held</th>
        </tr>
      </thead>
      <tbody>
        {keys.map((key) => (
          <tr key={key.keyid}>
            <td>{key.name || key.keyid_short}</td>
            <td>{key.signs.join(", ") || "—"}</td>
            <td>{key.online ? "RSTUF (online)" : "Offline"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
