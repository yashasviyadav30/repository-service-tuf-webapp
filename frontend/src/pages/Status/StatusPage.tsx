import { useStatus } from "./hooks/useStatus";
import { RepositoryStateBanner } from "./components/RepositoryStateBanner";
import { AwaitingSignaturesList } from "./components/AwaitingSignaturesList";
import { KeysTable } from "./components/KeysTable";

export function StatusPage() {
  const { data, loading, error, refresh } = useStatus();

  return (
    <section>
      <h1>Status</h1>
      <button onClick={refresh} disabled={loading}>
        Refresh
      </button>
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
