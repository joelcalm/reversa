import { Link } from "react-router-dom";
import { ArrowRight, Search } from "lucide-react";
import type { Summary } from "../../types";
import { KpiCard } from "../common";
import { ErrorView, Loading } from "../States";
import type { OverviewInsights } from "./overviewTypes";

interface Props {
  summary: Summary | null;
  insights: OverviewInsights | null;
  loading: boolean;
  error: string | null;
  onStartBriefing: () => void;
}

export default function OverviewHero({ summary, insights, loading, error, onStartBriefing }: Props) {
  if (loading) return <Loading message="Loading corpus overview…" />;
  if (error) return <ErrorView message={error} />;
  if (!summary || !insights) return null;

  const repealedTotal =
    (summary.lifecycle_counts?.REPEALED ?? 0) +
    (summary.lifecycle_counts?.ANNULLED ?? 0) +
    (summary.lifecycle_counts?.EXPIRED ?? 0);

  return (
    <section id="overview" className="overview-hero">
      <h1>Spain&apos;s statute book, mapped.</h1>
      <p className="overview-subtitle">
        {summary.total_norms.toLocaleString()} consolidated norms connected by{" "}
        {summary.total_relations.toLocaleString()} amendment, repeal and citation relationships.
      </p>
      <p className="overview-explain">
        Spanish legislation is not just a list of norms. It is a directed graph of amendments,
        repeals and citations. This platform shows where simplification should start.
      </p>

      <div className="overview-actions">
        <button type="button" className="btn" onClick={onStartBriefing}>
          Start Council Briefing <ArrowRight size={16} />
        </button>
        <Link to="/explorer" className="btn secondary">
          <Search size={16} /> Explore graph
        </Link>
      </div>

      <div className="kpi-grid overview-kpis">
        <KpiCard value={summary.total_norms.toLocaleString()} label="Norms ingested" />
        <KpiCard value={summary.total_relations.toLocaleString()} label="Relations" />
        <KpiCard value={(summary.lifecycle_counts?.LIVE ?? 0).toLocaleString()} label="Live norms" />
        <KpiCard value={repealedTotal.toLocaleString()} label="Repealed / annulled / expired" />
      </div>

      <div className="insight-grid">
        {insights.cards.map((card) => (
          <a key={card.anchor} href={`#${card.anchor}`} className="card insight-card">
            <div className="insight-action">{card.actionLabel}</div>
            <div className="insight-title">{card.title}</div>
            <div className="insight-number">{card.mainNumber}</div>
            <div className="insight-sub">{card.subtitle}</div>
          </a>
        ))}
      </div>

      <div className="legend overview-legend">
        <span className="item">
          <span className="swatch" style={{ background: "var(--color-live)" }} /> Live norm
        </span>
        <span className="item">
          <span className="swatch" style={{ background: "var(--color-repealed)" }} /> Repealed / annulled / expired
        </span>
        <span className="item">
          <span className="swatch line" style={{ background: "var(--color-amends)" }} /> AMENDS
        </span>
        <span className="item">
          <span className="swatch line cites-dash" /> CITES
        </span>
        <span className="item">
          <span className="swatch line" style={{ background: "var(--color-repeals)" }} /> REPEALS
        </span>
      </div>
    </section>
  );
}
