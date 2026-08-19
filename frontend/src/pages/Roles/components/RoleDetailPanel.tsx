// Populated view (name, version, status, expiry, signatures required,
// signed-by, delegates-to, raw file link) arrives once GET
// /api/v1/roles/{role} is wired in -- this PR only builds the two-column
// shell it plugs into.
export function RoleDetailPanel() {
  return <aside className="role-detail-panel">Select a role to see its details.</aside>;
}
