import { useStatus } from "./hooks/useStatus";
import { RepositoryStateBanner } from "./components/RepositoryStateBanner";
import { AwaitingSignaturesList } from "./components/AwaitingSignaturesList";
import { KeysTable } from "./components/KeysTable";

export function StatusPage() {
  const { data, loading, error } = useStatus();

  return (
    <section>
      <h1>Status</h1>
      {loading && <p>Loading status...</p>}
      {error && <p role="alert">{error}</p>}
      {data && (
        <>
          <RepositoryStateBanner available={data.available} state={data.state} message={data.message} />
          <AwaitingSignaturesList roles={data.awaiting_signatures} />
          <KeysTable keys={data.keys} />
        </>
      )}
    </section>
  );
}
