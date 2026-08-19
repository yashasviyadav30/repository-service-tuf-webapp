import type { RoleStatus, RoleSummary } from "../../../shared/overview/types";
import { ExpiryBadge } from "./ExpiryBadge";

interface RolesTableProps {
  roles: RoleSummary[];
  selectedRole: string | null;
  onSelectRole: (role: string) => void;
}

const STATUS_LABEL: Record<RoleStatus, string> = {
  valid: "Valid",
  expired: "Expired",
  invalid: "Invalid",
};

// "root_key_1, root_key_2 (2 of 2)" -- the count is how many keys are
// authorised versus the threshold, not how many have actually signed;
// RoleSummary doesn't carry a signed-count, only RoleDetailResponse does.
function signers(role: RoleSummary): string {
  if (role.key_names.length === 0) return "—";
  const names = role.key_names.join(", ");
  return role.threshold === null ? names : `${names} (${role.key_names.length} of ${role.threshold})`;
}

export function RolesTable({ roles, selectedRole, onSelectRole }: RolesTableProps) {
  return (
    <table className="roles-table">
      <thead>
        <tr>
          <th>Role</th>
          <th>Signers</th>
          <th>Ver.</th>
          <th>Expiry</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        {roles.map((role) => (
          <tr
            key={role.name}
            className={role.name === selectedRole ? "roles-table__row--selected" : undefined}
            onClick={() => onSelectRole(role.name)}
          >
            <td>{role.name}</td>
            <td>{signers(role)}</td>
            <td>{role.version}</td>
            <td>
              <ExpiryBadge band={role.band} label={role.expires_in} />
            </td>
            <td>{STATUS_LABEL[role.status]}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
