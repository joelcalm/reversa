import { useEffect, useState } from "react";
import { Search } from "lucide-react";
import { api } from "../api/client";
import { BoeLink, formatBoeDate, StatusPill } from "../components/common";
import GraphView, { GraphLegend } from "../graph/GraphView";
import { Empty, ErrorView, Loading } from "../components/States";
import type { GraphData, Norm } from "../types";

export default function GraphExplorer() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Norm[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [relationType, setRelationType] = useState("");
  const [graph, setGraph] = useState<GraphData | null>(null);
  const [detail, setDetail] = useState<Norm | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const search = async () => {
    setError(null);
    try {
      const res = await api.norms({ search: query, limit: 20 });
      setResults(res.items);
      if (res.items.length > 0) openNorm(res.items[0].id);
    } catch (e) {
      setError((e as Error).message);
    }
  };

  const openNorm = async (id: string) => {
    setSelectedId(id);
    setLoading(true);
    setError(null);
    try {
      const [g, d] = await Promise.all([
        api.neighborhood(id, relationType || undefined, 200),
        api.norm(id),
      ]);
      setGraph(g);
      setDetail(d);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  // Reload neighborhood when the relation-type filter changes.
  useEffect(() => {
    if (selectedId) openNorm(selectedId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [relationType]);

  return (
    <div>
      <div className="page-header">
        <h1>Graph explorer</h1>
      </div>
      <p className="explanation">
        Search a norm by title or BOE ID, then explore its neighborhood of amendments, repeals and
        citations. Click any node to inspect it. Subgraphs are built on the server so the full graph
        is never rendered at once.
      </p>

      <div className="toolbar">
        <input
          className="input"
          placeholder="Search by title or BOE ID (e.g. BOE-A-1992-26318)…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && search()}
          style={{ minWidth: 360, flex: 1 }}
        />
        <button className="btn" onClick={search}>
          <Search size={16} /> Search
        </button>
        <select
          className="input"
          value={relationType}
          onChange={(e) => setRelationType(e.target.value)}
          title="Filter by relation type"
        >
          <option value="">All relations</option>
          <option value="AMENDS">AMENDS</option>
          <option value="REPEALS">REPEALS</option>
          <option value="CITES">CITES</option>
          <option value="OTHER">OTHER</option>
        </select>
      </div>

      {results.length > 0 && (
        <div className="card card-pad" style={{ marginBottom: 16 }}>
          <div className="row-gap">
            {results.slice(0, 12).map((n) => (
              <button
                key={n.id}
                className={`btn secondary`}
                onClick={() => openNorm(n.id)}
                style={{
                  borderColor: selectedId === n.id ? "var(--color-green)" : undefined,
                  fontSize: 13,
                }}
              >
                {n.id}
              </button>
            ))}
          </div>
        </div>
      )}

      {error && <ErrorView message={error} />}

      <div className="layout-split">
        <div className="graph-shell">
          {loading && <Loading message="Loading neighborhood…" />}
          {!loading && !selectedId && <Empty message="Search and select a norm to explore." />}
          {!loading && selectedId && graph && graph.nodes.length === 0 && (
            <Empty message="No relations found for this norm and filter." />
          )}
          {!loading && graph && graph.nodes.length > 0 && (
            <>
              <GraphView data={graph} focusId={selectedId ?? undefined} layoutMode="explorer" onNodeClick={openNorm} height={520} />
              <GraphLegend />
            </>
          )}
        </div>

        <aside className="card side-panel">
          {detail ? (
            <>
              <h3>{detail.title ?? detail.id}</h3>
              <div style={{ marginBottom: 10 }}>
                <StatusPill status={detail.lifecycle_status} />
              </div>
              <div className="meta-row">
                <span className="k">BOE ID</span>
                <span>
                  <BoeLink norm={detail} />
                </span>
              </div>
              <div className="meta-row">
                <span className="k">Rank</span>
                <span>{detail.rank ?? "—"}</span>
              </div>
              <div className="meta-row">
                <span className="k">Department</span>
                <span style={{ textAlign: "right" }}>{detail.department ?? "—"}</span>
              </div>
              <div className="meta-row">
                <span className="k">Scope</span>
                <span>{detail.scope ?? "—"}</span>
              </div>
              <div className="meta-row">
                <span className="k">Published</span>
                <span>{formatBoeDate(detail.publication_date)}</span>
              </div>
              {detail.metrics && (
                <>
                  <div className="meta-row">
                    <span className="k">Amended by</span>
                    <span>{detail.metrics.amended_by_count ?? 0}</span>
                  </div>
                  <div className="meta-row">
                    <span className="k">Amends</span>
                    <span>{detail.metrics.amends_count ?? 0}</span>
                  </div>
                  <div className="meta-row">
                    <span className="k">Cites</span>
                    <span>{detail.metrics.cites_count ?? 0}</span>
                  </div>
                  <div className="meta-row">
                    <span className="k">Cited by</span>
                    <span>{detail.metrics.cited_by_count ?? 0}</span>
                  </div>
                </>
              )}
            </>
          ) : (
            <div className="muted">Node details will appear here.</div>
          )}
        </aside>
      </div>
    </div>
  );
}
