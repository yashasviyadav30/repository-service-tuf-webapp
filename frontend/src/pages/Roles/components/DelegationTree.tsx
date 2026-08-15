import type { DelegatedSummary, TreeEdge } from "../types/overview.types";

interface DelegationTreeProps {
  edges: TreeEdge[];
  delegated: DelegatedSummary[];
}

// OPEN QUESTION FOR SRINJOY: the architecture doc specs a React Flow graph
// here; his conventions spec didn't mention it either way. Left as a plain
// nested list for now -- props (edges, delegated) already match what a
// graph view would consume, so swapping the internals later shouldn't
// touch callers.
export function DelegationTree({ edges, delegated }: DelegationTreeProps) {
  const childrenOf = (parent: string) =>
    edges.filter((edge) => edge.parent === parent).map((edge) => edge.child);

  const versionOf = (name: string) => delegated.find((d) => d.name === name)?.version ?? null;

  return (
    <ul className="delegation-tree">
      {childrenOf("root").map((childName) => (
        <li key={childName}>
          {childName}
          {childrenOf(childName).length > 0 && (
            <ul>
              {childrenOf(childName).map((grandchild) => {
                const version = versionOf(grandchild);
                return (
                  <li key={grandchild}>
                    {grandchild}
                    {version !== null && <span> v{version}</span>}
                  </li>
                );
              })}
            </ul>
          )}
        </li>
      ))}
    </ul>
  );
}
