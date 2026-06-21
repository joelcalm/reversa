import { Link } from "react-router-dom";
import { api } from "../api/client";
import { KpiCard } from "../components/common";
import { ErrorView, Loading } from "../components/States";
import { useFetch } from "../components/useFetch";

const BRIEFINGS = [
  {
    num: "BRIEFING 1",
    to: "/briefings/unreadable",
    title: "Unreadable laws",
    desc: "Norms amended so many times they have become hard to read and maintain.",
  },
  {
    num: "BRIEFING 2",
    to: "/briefings/omnibus",
    title: "Omnibus laws",
    desc: "Single acts that quietly modified a large number of other norms.",
  },
  {
    num: "BRIEFING 3",
    to: "/briefings/dead-law",
    title: "Dead-law dependencies",
    desc: "How much of the live statute book still cites already-repealed law.",
  },
  {
    num: "BRIEFING 4",
    to: "/briefings/ley-30-1992",
    title: "Ley 30/1992 blast radius",
    desc: "Live norms that still cite the repealed Ley 30/1992 directly.",
  },
];

export default function Dashboard() {
  const { data: summary, loading, error } = useFetch(() => api.summary(), []);

  return (
    <div>
      <section className="hero">
        <h1>BOE Knowledge Graph</h1>
        <p className="subtitle">
          Mapping Spain's consolidated legislation as a graph of amendments, repeals and citations.
        </p>
        <span className="scope-note">Default scope: state-level consolidated norms (ámbito “Estatal”).</span>
      </section>

      {loading && <Loading message="Loading corpus summary…" />}
      {error && <ErrorView message={error} />}

      {summary && (
        <>
          <div className="kpi-grid">
            <KpiCard value={summary.total_norms.toLocaleString()} label="Norms ingested" />
            <KpiCard value={summary.total_relations.toLocaleString()} label="Relations" />
            <KpiCard
              value={(summary.lifecycle_counts?.LIVE ?? 0).toLocaleString()}
              label="Live norms"
            />
            <KpiCard
              value={(
                (summary.lifecycle_counts?.REPEALED ?? 0) +
                (summary.lifecycle_counts?.ANNULLED ?? 0) +
                (summary.lifecycle_counts?.EXPIRED ?? 0)
              ).toLocaleString()}
              label="Repealed / annulled / expired"
            />
          </div>

          <div className="card card-pad" style={{ marginBottom: 8 }}>
            <div className="row-gap" style={{ justifyContent: "space-between" }}>
              <div className="row-gap">
                {Object.entries(summary.relation_counts_by_type).map(([k, v]) => (
                  <span key={k} className="muted" style={{ fontSize: 13 }}>
                    <strong style={{ color: "var(--color-green-dark)" }}>{v.toLocaleString()}</strong>{" "}
                    {k}
                  </span>
                ))}
              </div>
              <span className="muted" style={{ fontSize: 13 }}>
                Last ingestion:{" "}
                {summary.last_ingestion_at
                  ? new Date(summary.last_ingestion_at).toLocaleString()
                  : "—"}
              </span>
            </div>
          </div>
        </>
      )}

      <div className="section-title">Executive briefings</div>
      <div className="briefing-grid">
        {BRIEFINGS.map((b) => (
          <Link key={b.to} to={b.to} className="card briefing-card">
            <span className="num">{b.num}</span>
            <h3>{b.title}</h3>
            <p>{b.desc}</p>
          </Link>
        ))}
      </div>

      <div className="section-title">About the data</div>
      <div className="card card-pad muted" style={{ fontSize: 14 }}>
        Relationships are normalized into a directed graph of{" "}
        <strong>AMENDS</strong>, <strong>REPEALS</strong>, <strong>CITES</strong> and{" "}
        <strong>OTHER</strong> edges, derived from each norm's <code>analisis/referencias</code>{" "}
        block. Lifecycle status is computed from the raw BOE status fields. All raw labels are kept
        for auditability. Data freshness above reflects the most recent ingestion run.
      </div>
    </div>
  );
}
