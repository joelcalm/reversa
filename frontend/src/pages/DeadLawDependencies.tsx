import { api } from "../api/client";
import BriefingGraph from "../components/BriefingGraph";
import { BoeLink, formatBoeDate, KpiCard, NormTitle, StatusPill } from "../components/common";
import { Column, SortableTable } from "../components/SortableTable";
import { ErrorView, Loading } from "../components/States";
import { useFetch } from "../components/useFetch";
import type { GhostNorm } from "../types";

const columns: Column<GhostNorm>[] = [
  { key: "rank", label: "#", render: (r) => <span className="rank-badge">{r.rank_position}</span> },
  { key: "id", label: "BOE ID", render: (r) => <BoeLink norm={r} />, sortValue: (r) => r.id },
  { key: "title", label: "Title (ghost norm)", render: (r) => <NormTitle norm={r} />, sortValue: (r) => r.title ?? "" },
  { key: "status", label: "Status", render: (r) => <StatusPill status={r.lifecycle_status} />, sortValue: (r) => r.lifecycle_status ?? "" },
  { key: "repeal", label: "Repeal date", render: (r) => formatBoeDate(r.repeal_date), sortValue: (r) => r.repeal_date ?? "" },
  {
    key: "citers",
    label: "Live citers",
    numeric: true,
    render: (r) => r.live_citers,
    sortValue: (r) => r.live_citers,
  },
];

export default function DeadLawDependencies() {
  const { data, loading, error } = useFetch(() => api.deadLaw("state", 5), []);

  return (
    <div>
      <div className="page-header">
        <span className="scope-note">Scope: state-level norms · CITES edges only</span>
        <h1 style={{ marginTop: 12 }}>Briefing 3 — Dead-law dependencies</h1>
      </div>
      <p className="explanation">
        How much of the statute book rests on dead law? This measures the share of{" "}
        <strong>live norms that cite at least one already-repealed norm</strong>. Only citation-type
        references are counted — amendments and repeals are deliberately excluded.
      </p>

      {loading && <Loading />}
      {error && <ErrorView message={error} />}
      {data && (
        <>
          <div className="kpi-grid">
            <KpiCard value={`${data.percentage}%`} label="of live norms cite repealed norms" />
            <KpiCard
              value={data.live_norms_citing_repealed_count.toLocaleString()}
              label="Live norms citing dead law (numerator)"
            />
            <KpiCard
              value={data.live_norms_count.toLocaleString()}
              label="Live norms in scope (denominator)"
            />
            <KpiCard value={data.top_ghost_norms.length} label="Ghost norms ranked" />
          </div>

          <div className="section-title">
            Top ghost norms — repealed norms most cited by live norms (top 5)
          </div>
          {data.top_ghost_norms.length > 0 ? (
            <SortableTable columns={columns} rows={data.top_ghost_norms} initialSort="citers" />
          ) : (
            <div className="card card-pad muted">No live norms cite repealed norms in this scope.</div>
          )}

          <div className="section-title">Subgraph — live citers and the repealed ghosts they cite</div>
          <BriefingGraph briefingKey="dead-law-dependencies" scope="state" />
        </>
      )}
    </div>
  );
}
