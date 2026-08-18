interface AwaitingSignaturesListProps {
  roles: string[];
}

// Only ever non-empty while state is "awaiting_signatures", but takes the
// plain list rather than the whole StatusResponse -- keeps this component
// usable without pulling in the state enum it doesn't otherwise need.
export function AwaitingSignaturesList({ roles }: AwaitingSignaturesListProps) {
  if (roles.length === 0) return null;

  return (
    <div className="awaiting-signatures">
      <h2>Awaiting signatures</h2>
      <ul>
        {roles.map((role) => (
          <li key={role}>{role}</li>
        ))}
      </ul>
    </div>
  );
}
