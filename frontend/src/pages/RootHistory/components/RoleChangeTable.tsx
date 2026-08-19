import type { RootRoleChange } from "../types/roots.types";

interface RoleChangeTableProps {
  changes: RootRoleChange[];
}

function threshold(change: RootRoleChange): string {
  if (change.threshold_before === null) return `${change.threshold_after ?? "—"}`;
  if (change.threshold_after === null) return `${change.threshold_before}`;
  return change.threshold_before === change.threshold_after
    ? `${change.threshold_after}`
    : `${change.threshold_before} → ${change.threshold_after}`;
}

function signers(change: RootRoleChange): string {
  const parts = [...change.signers_added.map((name) => `+${name}`), ...change.signers_removed.map((name) => `-${name}`)];
  return parts.length > 0 ? parts.join(", ") : "—";
}

export function RoleChangeTable({ changes }: RoleChangeTableProps) {
  return (
    <table className="role-change-table">
      <thead>
        <tr>
          <th>Role</th>
          <th>Signatures required</th>
          <th>Signers</th>
        </tr>
      </thead>
      <tbody>
        {changes.map((change) => (
          <tr key={change.role}>
            <td>{change.role}</td>
            <td>{threshold(change)}</td>
            <td>{signers(change)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
