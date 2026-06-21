import { api } from "../api/client";
import { Column, SortableTable } from "../components/SortableTable";
import { ErrorView, Loading } from "../components/States";
import { useFetch } from "../components/useFetch";

export default function DataQuality() {
  const { data, loading, error } = useFetch(() => api.dataQuality(100), []);

  const labelColumns: Column<{ label: string; normalized_type: string; count: number }>[] = [
    { key: "label", label: "Raw BOE label", render: (r) => r.label, sortValue: (r) => r.label },
    {
      key: "type",
      label: "Normalized type",
      render: (r) => r.normalized_type,
      sortValue: (r) => r.normalized_type,
    },
    { key: "count", label: "Count", numeric: true, render: (r) => r.count, sortValue: (r) => r.count },
  ];

  return (
    <div>
      <div className="page-header">
        <h1>Data quality</h1>
        <p className="explanation">
          Engineering audit of the ingested corpus: relation counts, label normalization, and
          unresolved citation targets. This page supports trust in briefing numbers — not a legal
          product surface.
        </p>
      </div>

      {loading && <Loading message="Loading data quality report…" />}
      {error && <ErrorView message={error} />}
      {data && (
        <>
          <div className="kpi-grid">
            <div className="card kpi">
              <div className="kpi-value">{data.total_norms.toLocaleString()}</div>
              <div className="kpi-label">Norms ingested</div>
            </div>
            <div className="card kpi">
              <div className="kpi-value">{data.total_relations.toLocaleString()}</div>
              <div className="kpi-label">Relations</div>
            </div>
            <div className="card kpi">
              <div className="kpi-value">{data.distinct_raw_labels.toLocaleString()}</div>
              <div className="kpi-label">Distinct raw relation labels</div>
            </div>
            <div className="card kpi">
              <div className="kpi-value">{data.unknown_target_relations.toLocaleString()}</div>
              <div className="kpi-label">Relations with unknown targets</div>
            </div>
            <div className="card kpi">
              <div className="kpi-value">{data.other_label_occurrences.toLocaleString()}</div>
              <div className="kpi-label">OTHER label occurrences</div>
            </div>
            <div className="card kpi">
              <div className="kpi-value">
                {data.last_ingestion_at
                  ? new Date(data.last_ingestion_at).toLocaleString()
                  : "—"}
              </div>
              <div className="kpi-label">Last ingestion</div>
            </div>
          </div>

          <div className="section-title">Relation types (normalized)</div>
          <div className="card card-pad">
            <ul className="relation-breakdown">
              {Object.entries(data.relation_counts_by_type).map(([k, v]) => (
                <li key={k}>
                  <strong>{k}</strong>: {v.toLocaleString()}
                </li>
              ))}
            </ul>
          </div>

          <div className="section-title">
            Raw label normalization (top {data.label_limit} of {data.distinct_raw_labels})
          </div>
          <SortableTable columns={labelColumns} rows={data.labels} initialSort="count" pageSize={25} />

          <p className="muted context-note" style={{ marginTop: 24 }}>
            Unknown targets are citation edges where the target norm ID could not be resolved in the
            corpus. Failed API retries during ingestion are not persisted and are not shown here.
          </p>
        </>
      )}
    </div>
  );
}
