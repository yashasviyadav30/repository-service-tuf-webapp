import { useOverview } from "./hooks/useOverview";
import { StatusBanner } from "./components/StatusBanner";
import { RolesTable } from "./components/RolesTable";
import { DelegationTree } from "./components/DelegationTree";

export function RolesPage() {
  const { data, loading, error, refresh } = useOverview();

  return (
    <section>
      <h1>Roles</h1>
      <button onClick={refresh} disabled={loading}>
        Refresh
      </button>
      {loading && <p>Loading metadata...</p>}
      {error && <p role="alert">{error}</p>}
      {data && (
        <>
          <StatusBanner
            status={data.status}
            verificationError={data.verification_error}
            checkedAt={data.checked_at}
          />
          <RolesTable roles={data.roles} />
          <DelegationTree edges={data.edges} delegated={data.delegated} />
        </>
      )}
    </section>
  );
}
