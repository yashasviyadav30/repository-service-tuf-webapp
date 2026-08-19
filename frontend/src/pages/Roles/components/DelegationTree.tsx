import { useState } from "react";
import type { DelegatedSummary, TreeEdge } from "../../../shared/overview/types";

interface DelegationTreeProps {
  edges: TreeEdge[];
  delegated: DelegatedSummary[];
  selectedRole: string | null;
  onSelectRole: (role: string) => void;
}

// OPEN QUESTION FOR SRINJOY: the architecture doc specs a React Flow graph
// here; his conventions spec didn't mention it either way. Left as a plain
// nested list for now -- props already match what a graph view would
// consume, so swapping the internals later shouldn't touch callers.
export function DelegationTree({ edges, delegated, selectedRole, onSelectRole }: DelegationTreeProps) {
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  const childrenOf = (parent: string) =>
    edges.filter((edge) => edge.parent === parent).map((edge) => edge.child);
  const isDelegated = (name: string) => delegated.some((d) => d.name === name);
  const versionOf = (name: string) => delegated.find((d) => d.name === name)?.version ?? null;

  const nodeButton = (name: string, label: string) => (
    <button
      type="button"
      className={`tree-node${name === selectedRole ? " tree-node--selected" : ""}`}
      onClick={() => onSelectRole(name)}
    >
      {label}
    </button>
  );

  return (
    <ul className="delegation-tree">
      {childrenOf("root").map((childName) => {
        const bins = childrenOf(childName).filter(isDelegated);
        const isExpanded = expanded.has(childName);

        return (
          <li key={childName}>
            {nodeButton(childName, childName)}
            {bins.length > 0 && (
              <ul>
                {isExpanded ? (
                  bins.map((bin) => {
                    const version = versionOf(bin);
                    return <li key={bin}>{nodeButton(bin, version !== null ? `${bin} v${version}` : bin)}</li>;
                  })
                ) : (
                  <li>
                    <button type="button" onClick={() => setExpanded((prev) => new Set(prev).add(childName))}>
                      {bins.length} delegated role{bins.length === 1 ? "" : "s"} / click to expand
                    </button>
                  </li>
                )}
              </ul>
            )}
          </li>
        );
      })}
    </ul>
  );
}
