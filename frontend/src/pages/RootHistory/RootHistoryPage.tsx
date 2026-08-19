import { useRoots } from "./hooks/useRoots";
import { VersionTimeline } from "./components/VersionTimeline";

export function RootHistoryPage() {
  const { data, loading, error } = useRoots();

  return (
    <section>
      <h1>Root history</h1>
      {loading && <p>Loading root history...</p>}
      {error && <p role="alert">{error}</p>}
      {data && (
        <>
          {data.message && <p className="root-history-message">{data.message}</p>}
          <VersionTimeline versions={data.versions} />
        </>
      )}
    </section>
  );
}
