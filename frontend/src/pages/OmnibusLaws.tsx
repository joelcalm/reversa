import { api } from "../api/client";
import BriefingGraph from "../components/BriefingGraph";
import { BoeLink, formatBoeDate, NormTitle, StatusPill } from "../components/common";
import { Column, SortableTable } from "../components/SortableTable";
import { ErrorView, Loading } from "../components/States";
import { useFetch } from "../components/useFetch";
import type { OmnibusItem } from "../types";

const columns: Column<OmnibusItem>[] = [
  { key: "rank", label: "#", render: (r) => <span className="rank-badge">{r.rank_position}</span> },
  { key: "id", label: "BOE ID", render: (r) => <BoeLink norm={r} />, sortValue: (r) => r.id },
  { key: "title", label: "Title", render: (r) => <NormTitle norm={r} />, sortValue: (r) => r.title ?? "" },
  { key: "rankName", label: "Rank", render: (r) => r.rank ?? "—", sortValue: (r) => r.rank ?? "" },
  { key: "dept", label: "Department", render: (r) => r.department ?? "—", sortValue: (r) => r.department ?? "" },
  { key: "pub", label: "Published", render: (r) => formatBoeDate(r.publication_date), sortValue: (r) => r.publication_date ?? "" },
  { key: "status", label: "Status", render: (r) => <StatusPill status={r.lifecycle_status} />, sortValue: (r) => r.lifecycle_status ?? "" },
  {
    key: "diversity",
    label: "Subject diversity",
    numeric: true,
    render: (r) => r.subject_diversity ?? 0,
    sortValue: (r) => r.subject_diversity ?? 0,
  },
  {
    key: "count",
    label: "Norms amended",
    numeric: true,
    render: (r) => r.target_count,
    sortValue: (r) => r.target_count,
  },
];

export default function OmnibusLaws() {
  const { data, loading, error } = useFetch(() => api.omnibus("state", 5), []);

  return (
    <div>
      <div className="page-header">
        <span className="scope-note">Scope: state-level norms</span>
        <h1 style={{ marginTop: 12 }}>Briefing 2 — Omnibus laws</h1>
      </div>
      <p className="explanation">
        Omnibus norms are single acts that modify many other norms. This ranks norms by the number
        of <strong>distinct norms they amend</strong> (outgoing AMENDS edges). Subject diversity is
        the count of distinct subjects across the amended norms.
      </p>

      {loading && <Loading />}
      {error && <ErrorView message={error} />}
      {data && (
        <>
          <div className="section-title">Rankings — top 5 omnibus norms (most norms amended)</div>
          <SortableTable columns={columns} rows={data.items} initialSort="count" />
          <div className="section-title">Subgraph — outgoing amendments from the omnibus norms</div>
          <BriefingGraph briefingKey="omnibus-laws" scope="state" />
        </>
      )}
    </div>
  );
}
