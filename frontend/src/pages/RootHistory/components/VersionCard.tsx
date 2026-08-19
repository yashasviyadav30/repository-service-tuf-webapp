import type { RootVersionSummary } from "../types/roots.types";
import { RoleChangeTable } from "./RoleChangeTable";

interface VersionCardProps {
  version: RootVersionSummary;
  supersededBy: number | null;
}

export function VersionCard({ version, supersededBy }: VersionCardProps) {
  return (
    <li className="root-version-card">
      <h2>
        Version {version.version}
        {version.superseded ? ` -- superseded by version ${supersededBy}` : " -- in force"}
      </h2>
      <ul className="root-version-card__checks">
        <li>
          Signed by its own keys: {version.by_own_keys.present} of {version.by_own_keys.threshold} required
        </li>
        {version.by_previous_keys && (
          <li>
            Authorised by version {version.version - 1}: {version.by_previous_keys.present} of{" "}
            {version.by_previous_keys.threshold} required
          </li>
        )}
      </ul>
      {version.note && <p>{version.note}</p>}
      {version.keys_changed.length > 0 && (
        <ul className="root-version-card__key-diff">
          {version.keys_changed.map((change) => (
            <li key={change.keyid} className={`key-diff key-diff--${change.action}`}>
              {change.action === "added" ? (
                `+ ${change.name} (${change.keyid_short})`
              ) : (
                <s>
                  {change.name} ({change.keyid_short})
                </s>
              )}
            </li>
          ))}
        </ul>
      )}
      {version.roles_changed.length > 0 && <RoleChangeTable changes={version.roles_changed} />}
    </li>
  );
}
