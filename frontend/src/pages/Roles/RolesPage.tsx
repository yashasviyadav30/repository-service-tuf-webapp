import { useOverviewContext } from "../../shared/overview/OverviewContext";
import { RolesTable } from "./components/RolesTable";
import { DelegationTree } from "./components/DelegationTree";

export function RolesPage() {
  const { data, loading, error } = useOverviewContext();

  return (
    <section>
      <h1>Roles</h1>
      {loading && <p>Loading metadata...</p>}
      {error && <p role="alert">{error}</p>}
      {data && (
        <>
          <RolesTable roles={data.roles} />
          <DelegationTree edges={data.edges} delegated={data.delegated} />
        </>
      )}
    </section>
  );
}
