import type { ReactNode } from "react";
import { BoeLink, formatBoeDate, StatusPill } from "../common";
import type { Norm } from "../../types";
import type { Recommendation } from "../../utils/recommendations";

interface Props {
  norm?: Norm | null;
  recommendation?: Recommendation | null;
  extra?: ReactNode;
  loading?: boolean;
}

export default function RecommendationPanel({ norm, recommendation, extra, loading }: Props) {
  if (loading) {
    return (
      <aside className="card recommendation-panel card-pad">
        <div className="muted">Loading details…</div>
      </aside>
    );
  }
  if (!norm) {
    return (
      <aside className="card recommendation-panel card-pad">
        <div className="muted">Select a norm from the table or graph.</div>
      </aside>
    );
  }

  return (
    <aside className="card recommendation-panel card-pad">
      <h3 className="rec-title">{norm.title ?? norm.id}</h3>
      <div style={{ marginBottom: 12 }}>
        <StatusPill status={norm.lifecycle_status} />
      </div>
      <div className="meta-row">
        <span className="k">BOE ID</span>
        <BoeLink norm={norm} />
      </div>
      <div className="meta-row">
        <span className="k">Rank</span>
        <span>{norm.rank ?? "—"}</span>
      </div>
      <div className="meta-row">
        <span className="k">Department</span>
        <span style={{ textAlign: "right" }}>{norm.department ?? "—"}</span>
      </div>
      <div className="meta-row">
        <span className="k">Published</span>
        <span>{formatBoeDate(norm.publication_date)}</span>
      </div>

      {extra}

      {recommendation && (
        <div className="rec-action-block">
          <div className="rec-action-label">Recommended action</div>
          <div className="rec-action-title">{recommendation.label}</div>
          <p className="rec-action-reason">{recommendation.reason}</p>
        </div>
      )}
    </aside>
  );
}
