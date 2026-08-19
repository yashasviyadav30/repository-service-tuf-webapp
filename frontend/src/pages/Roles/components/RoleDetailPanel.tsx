import { useRole } from "../hooks/useRole";
import { STATUS_LABEL } from "./RolesTable";

interface RoleDetailPanelProps {
  selectedRole: string | null;
}

export function RoleDetailPanel({ selectedRole }: RoleDetailPanelProps) {
  const { data, loading, error } = useRole(selectedRole);

  if (!selectedRole) {
    return <aside className="role-detail-panel">Select a role to see its details.</aside>;
  }
  if (loading) {
    return <aside className="role-detail-panel">Loading {selectedRole}...</aside>;
  }
  if (error) {
    return (
      <aside className="role-detail-panel" role="alert">
        {error}
      </aside>
    );
  }
  if (!data) return null;

  return (
    <aside className="role-detail-panel">
      <h2>{data.name}</h2>
      <dl>
        <dt>Version</dt>
        <dd>{data.version}</dd>
        <dt>Status</dt>
        <dd>{STATUS_LABEL[data.status]}</dd>
        <dt>Expiry</dt>
        <dd>{data.expires_in}</dd>
        <dt>Signatures required</dt>
        <dd>{data.threshold === null ? "—" : `${data.signatures_present ?? 0} of ${data.threshold}`}</dd>
        {data.signature_note && (
          <>
            <dt>Signature note</dt>
            <dd>{data.signature_note}</dd>
          </>
        )}
        <dt>Signed by</dt>
        <dd>{data.signed_by.length > 0 ? data.signed_by.map((key) => key.name || key.keyid_short).join(", ") : "—"}</dd>
        <dt>Delegates to</dt>
        <dd>{data.delegates_to.length > 0 ? data.delegates_to.join(", ") : "—"}</dd>
      </dl>
      {data.raw_url && (
        <a href={data.raw_url} target="_blank" rel="noreferrer">
          View signed file
        </a>
      )}
    </aside>
  );
}
