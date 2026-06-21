import { api } from "../api/client";
import BriefingGraph from "../components/BriefingGraph";
import { BoeLink, formatBoeDate, NormTitle, StatusPill } from "../components/common";
import { Column, SortableTable } from "../components/SortableTable";
import { ErrorView, Loading } from "../components/States";
import { useFetch } from "../components/useFetch";
import type { UnreadableItem } from "../types";

const columns: Column<UnreadableItem>[] = [
  { key: "rank", label: "#", render: (r) => <span className="rank-badge">{r.rank_position}</span> },
  { key: "id", label: "BOE ID", render: (r) => <BoeLink norm={r} />, sortValue: (r) => r.id },
  { key: "title", label: "Title", render: (r) => <NormTitle norm={r} />, sortValue: (r) => r.title ?? "" },
  { key: "rankName", label: "Rank", render: (r) => r.rank ?? "—", sortValue: (r) => r.rank ?? "" },
  { key: "dept", label: "Department", render: (r) => r.department ?? "—", sortValue: (r) => r.department ?? "" },
  { key: "pub", label: "Published", render: (r) => formatBoeDate(r.publication_date), sortValue: (r) => r.publication_date ?? "" },
  { key: "status", label: "Status", render: (r) => <StatusPill status={r.lifecycle_status} />, sortValue: (r) => r.lifecycle_status ?? "" },
  {
    key: "count",
    label: "Distinct amending norms",
    numeric: true,
    render: (r) => r.amending_count,
    sortValue: (r) => r.amending_count,
  },
];

export default function UnreadableLaws() {
  const { data, loading, error } = useFetch(() => api.unreadable("state", 5), []);

  return (
    <div>
      <div className="page-header">
        <span className="scope-note">Scope: state-level norms</span>
        <h1 style={{ marginTop: 12 }}>Briefing 1 — Unreadable laws</h1>
      </div>
      <p className="explanation">
        Norms amended many times become hard to understand and maintain. This ranks norms by the
        number of <strong>distinct other norms that amend them</strong> (one count per amending
        norm, even if it amended the same target several times).
      </p>

      {loading && <Loading />}
      {error && <ErrorView message={error} />}
      {data && (
        <>
          <div className="section-title">Rankings — top 5 norms most amended by others</div>
          <SortableTable columns={columns} rows={data.items} initialSort="count" />
          <div className="section-title">Subgraph — incoming amendments to the top norms</div>
          <BriefingGraph briefingKey="unreadable-laws" scope="state" />
        </>
      )}
    </div>
  );
}
