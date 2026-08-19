import type { ArtifactSummary } from "../types/artifacts.types";

interface ArtifactsTableProps {
  artifacts: ArtifactSummary[];
}

// length is raw bytes from the schema -- humanized here since the backend
// doesn't pre-format it the way expires_in pre-formats a date.
function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

// hashes is a bare Record<string, string> -- "sha256" is the TUF-spec key
// name for this algorithm, not a guess, but its presence isn't guaranteed.
function shortHash(hashes: Record<string, string>): string {
  const sha256 = hashes.sha256;
  return sha256 ? sha256.slice(0, 12) : "—";
}

export function ArtifactsTable({ artifacts }: ArtifactsTableProps) {
  return (
    <table className="artifacts-table">
      <thead>
        <tr>
          <th>Path</th>
          <th>Role</th>
          <th>Size</th>
          <th>SHA-256</th>
        </tr>
      </thead>
      <tbody>
        {artifacts.map((artifact) => (
          <tr key={artifact.path}>
            <td>{artifact.path}</td>
            <td>{artifact.role}</td>
            <td>{formatSize(artifact.length)}</td>
            <td className="artifacts-table__hash">{shortHash(artifact.hashes)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
