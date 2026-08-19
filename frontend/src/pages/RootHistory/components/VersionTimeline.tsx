import type { RootVersionSummary } from "../types/roots.types";
import { VersionCard } from "./VersionCard";

interface VersionTimelineProps {
  versions: RootVersionSummary[];
}

// Newest first, already the order the API returns -- "superseded by" is
// derived from list position (the entry one newer), not a field the
// schema provides.
export function VersionTimeline({ versions }: VersionTimelineProps) {
  return (
    <ul className="root-version-timeline">
      {versions.map((version, index) => (
        <VersionCard
          key={version.version}
          version={version}
          supersededBy={index > 0 ? versions[index - 1].version : null}
        />
      ))}
    </ul>
  );
}
