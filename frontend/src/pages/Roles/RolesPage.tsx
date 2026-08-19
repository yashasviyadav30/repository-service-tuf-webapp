import { useState } from "react";
import { useOverviewContext } from "../../shared/overview/OverviewContext";
import { RolesTable } from "./components/RolesTable";
import { DelegationTree } from "./components/DelegationTree";
import { RoleDetailPanel } from "./components/RoleDetailPanel";

export function RolesPage() {
  const { data, loading, error } = useOverviewContext();
  const [selectedRole, setSelectedRole] = useState<string | null>(null);

  return (
    <section>
      <h1>Roles</h1>
      {loading && <p>Loading metadata...</p>}
      {error && <p role="alert">{error}</p>}
      {data && (
        <div className="roles-page__layout">
          <div className="roles-page__list">
            <RolesTable roles={data.roles} selectedRole={selectedRole} onSelectRole={setSelectedRole} />
            <DelegationTree
              edges={data.edges}
              delegated={data.delegated}
              selectedRole={selectedRole}
              onSelectRole={setSelectedRole}
            />
          </div>
          <RoleDetailPanel selectedRole={selectedRole} />
        </div>
      )}
    </section>
  );
}
