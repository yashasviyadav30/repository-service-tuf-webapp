import { useArtifacts } from "./hooks/useArtifacts";
import { SearchBox } from "./components/SearchBox";
import { Pagination } from "./components/Pagination";
import { ArtifactsTable } from "./components/ArtifactsTable";

export function ArtifactsPage() {
  const { data, loading, error, search, setSearch, setPage } = useArtifacts();

  return (
    <section>
      <h1>Artifacts</h1>
      <SearchBox value={search} onChange={setSearch} />
      {loading && <p>Loading artifacts...</p>}
      {error && <p role="alert">{error}</p>}
      {data && (
        <>
          <ArtifactsTable artifacts={data.artifacts} />
          <Pagination page={data.page} pageSize={data.page_size} total={data.total} onPageChange={setPage} />
        </>
      )}
    </section>
  );
}
