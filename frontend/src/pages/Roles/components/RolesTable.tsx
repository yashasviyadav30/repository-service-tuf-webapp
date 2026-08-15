import type { RoleSummary } from "../types/overview.types";
import { ExpiryBadge } from "./ExpiryBadge";

interface RolesTableProps {
  roles: RoleSummary[];
}

export function RolesTable({ roles }: RolesTableProps) {
  return (
    <table className="roles-table">
      <thead>
        <tr>
          <th>Role</th>
          <th>Version</th>
          <th>Expires</th>
          <th>Threshold</th>
          <th>Signers</th>
        </tr>
      </thead>
      <tbody>
        {roles.map((role) => (
          <tr key={role.name}>
            <td>{role.name}</td>
            <td>{role.version}</td>
            <td>
              <ExpiryBadge band={role.band} label={role.expires_in} />
            </td>
            <td>{role.threshold ?? "—"}</td>
            <td>{role.key_names.join(", ") || "—"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
