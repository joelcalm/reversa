import { useMemo, useState } from "react";
import { Download } from "lucide-react";
import { api } from "../api/client";
import BriefingGraph from "../components/BriefingGraph";
import { BoeLink, formatBoeDate, KpiCard, NormTitle, StatusPill } from "../components/common";
import { Column, SortableTable } from "../components/SortableTable";
import { ErrorView, Loading } from "../components/States";
import { useFetch } from "../components/useFetch";
import type { CitingNorm } from "../types";
import { downloadCsv, toCsv } from "../utils/csv";

const columns: Column<CitingNorm>[] = [
  { key: "rank", label: "#", render: (r) => <span className="rank-badge">{r.rank_position}</span> },
  { key: "id", label: "BOE ID", render: (r) => <BoeLink norm={r} />, sortValue: (r) => r.id },
  { key: "title", label: "Title", render: (r) => <NormTitle norm={r} />, sortValue: (r) => r.title ?? "" },
  { key: "rankName", label: "Rank", render: (r) => r.rank ?? "—", sortValue: (r) => r.rank ?? "" },
  { key: "dept", label: "Department", render: (r) => r.department ?? "—", sortValue: (r) => r.department ?? "" },
  { key: "pub", label: "Published", render: (r) => formatBoeDate(r.publication_date), sortValue: (r) => r.publication_date ?? "" },
  { key: "status", label: "Status", render: (r) => <StatusPill status={r.lifecycle_status} />, sortValue: (r) => r.lifecycle_status ?? "" },
  {
    key: "relation",
    label: "Relation (raw)",
    render: (r) => <span className="muted">{r.relation_label_raw ?? "—"}</span>,
    sortValue: (r) => r.relation_label_raw ?? "",
  },
];

export default function BlastRadius() {
  const { data, loading, error } = useFetch(() => api.blastRadius("state"), []);
  const [filter, setFilter] = useState("");

  const filtered = useMemo(() => {
    if (!data) return [];
    const q = filter.trim().toLowerCase();
    if (!q) return data.citing_norms;
    return data.citing_norms.filter(
      (n) =>
        n.id.toLowerCase().includes(q) ||
        (n.title ?? "").toLowerCase().includes(q) ||
        (n.department ?? "").toLowerCase().includes(q)
    );
  }, [data, filter]);

  const exportCsv = () => {
    if (!data) return;
    const csv = toCsv(
      ["rank", "boe_id", "title", "rank_name", "department", "published", "status", "relation_raw", "url"],
      data.citing_norms.map((n) => [
        n.rank_position ?? "",
        n.id,
        n.title ?? "",
        n.rank ?? "",
        n.department ?? "",
        formatBoeDate(n.publication_date),
        n.lifecycle_status ?? "",
        n.relation_label_raw ?? "",
        n.url_html ?? "",
      ])
    );
    downloadCsv("ley-30-1992-blast-radius.csv", csv);
  };

  return (
    <div>
      <div className="page-header">
        <span className="scope-note">Scope: state-level norms · CITES edges only</span>
        <h1 style={{ marginTop: 12 }}>Briefing 4 — The unfinished repeal: Ley 30/1992</h1>
      </div>
      <p className="explanation">
        In 2015, Ley 30/1992 was repealed and replaced by Leyes 39/2015 and 40/2015 — yet live norms
        may still cite it directly. This is the full worklist of{" "}
        <strong>live norms that directly cite Ley 30/1992</strong> (
        <a href="https://www.boe.es/buscar/act.php?id=BOE-A-1992-26318" target="_blank" rel="noreferrer">
          BOE-A-1992-26318
        </a>
        ).
      </p>

      {loading && <Loading />}
      {error && <ErrorView message={error} />}
      {data && (
        <>
          <div className="kpi-grid">
            <KpiCard value={data.total_live_direct_citers} label="Live norms citing Ley 30/1992" />
            <KpiCard
              value={<StatusPill status={data.ley_30_1992?.lifecycle_status} />}
              label="Status of Ley 30/1992"
            />
            <KpiCard value={formatBoeDate(data.ley_30_1992?.repeal_date)} label="Repeal date" />
          </div>

          <div className="toolbar">
            <input
              className="input"
              placeholder="Filter worklist by id, title or department…"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              style={{ minWidth: 320, flex: 1 }}
            />
            <button className="btn" onClick={exportCsv} disabled={!data.citing_norms.length}>
              <Download size={16} /> Download CSV
            </button>
          </div>

          {filtered.length > 0 ? (
            <SortableTable columns={columns} rows={filtered} initialSort="pub" />
          ) : (
            <div className="card card-pad muted">No live norms match the current filter / scope.</div>
          )}

          <div className="section-title">Subgraph — incoming citations to Ley 30/1992 from live norms</div>
          <BriefingGraph briefingKey="ley-30-1992-blast-radius" scope="state" focusId={data.target_id} />
        </>
      )}
    </div>
  );
}
