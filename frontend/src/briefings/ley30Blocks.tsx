import type { ReactNode } from "react";
import { formatBoeDate, InfoTip, StatusPill } from "../components/common";
import { ErrorView, Loading } from "../components/States";
import { useFetch } from "../components/useFetch";
import { api } from "../api/client";
import type { CleanupImpact, RepealContext } from "../types";
import { EvidenceButton } from "../components/common";

export function RepealContextBlock({ ctx }: { ctx: RepealContext }) {
  const fullRepealer = ctx.repealing_norms.find((r) => r.is_full_repeal) ?? ctx.repealing_norms[0];
  return (
    <div className="card card-pad repeal-context-block">
      <div className="section-title" style={{ marginTop: 0 }}>
        Repeal &amp; replacement context
      </div>
      <div className="context-card">
        <div className="card context-item">
          <div className="ctx-label">Status</div>
          <div className="ctx-value">
            <StatusPill status={ctx.status} />
          </div>
        </div>
        <div className="card context-item">
          <div className="ctx-label">2015 replacement context</div>
          <div className="ctx-value" style={{ fontSize: 13.5 }}>
            {ctx.replacement_norms.map((r) => (
              <div key={r.id} style={{ marginBottom: 4 }}>
                <a href={r.url_html} target="_blank" rel="noreferrer">
                  {r.title?.split(",")[0]}
                </a>
                <span className="muted"> — {r.role.split("(")[0].trim()}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="card context-item">
          <div className="ctx-label">
            BOE raw repeal-date field{" "}
            <InfoTip
              text={
                <>
                  <strong>{formatBoeDate(ctx.boe_raw_repeal_date?.replace(/-/g, ""))}</strong> is the
                  raw BOE <code>fecha_derogacion</code> field — when deferred 2015 provisions took
                  effect, not necessarily when replacement began.
                  {fullRepealer && (
                    <>
                      {" "}
                      Graph evidence: <em>{fullRepealer.relation_label_raw}</em>{" "}
                      {fullRepealer.relation_detail_raw}.
                    </>
                  )}
                </>
              }
            />
          </div>
          <div className="ctx-value">
            {ctx.boe_raw_repeal_date ? (
              formatBoeDate(ctx.boe_raw_repeal_date.replace(/-/g, ""))
            ) : (
              <span className="muted">Not present</span>
            )}
          </div>
        </div>
      </div>
      <div className="context-note">{ctx.display_note}</div>
    </div>
  );
}

export function CleanupImpactCard({
  scope,
  onEvidence,
}: {
  scope: string;
  onEvidence: () => void;
}) {
  const { data, loading, error } = useFetch(() => api.cleanupImpact(scope), [scope]);
  if (loading) return <Loading message="Simulating cleanup impact…" />;
  if (error) return <ErrorView message={error} />;
  if (!data) return null;
  return <CleanupImpactContent data={data} onEvidence={onEvidence} />;
}

function CleanupImpactContent({
  data,
  onEvidence,
}: {
  data: CleanupImpact;
  onEvidence: () => void;
}) {
  const after = data.after_simulated_cleanup;
  return (
    <div className="card card-pad cleanup-impact-block">
      <div className="section-title" style={{ marginTop: 0 }}>
        Cleanup impact simulator{" "}
        <InfoTip text="Simulation removes only direct CITES edges to Ley 30/1992 and recomputes live norms still citing any dead norm." />
      </div>
      <div className="impact-flow">
        <div className="impact-stat before">
          <div className="big">{data.before.percentage}%</div>
          <div className="lbl">
            Before · {data.before.live_norms_citing_dead_law.toLocaleString()} live norms on dead law
          </div>
        </div>
        <div className="impact-arrow">→</div>
        <div className="impact-stat">
          <div className="big">{after.percentage}%</div>
          <div className="lbl">
            After · {after.live_norms_still_citing_dead_law.toLocaleString()} still on dead law
          </div>
        </div>
        <div className="impact-arrow">·</div>
        <div className="impact-stat">
          <div className="big">{after.fully_cleaned_norms.toLocaleString()}</div>
          <div className="lbl">Fully cleaned by this cleanup</div>
        </div>
        <div className="impact-arrow">·</div>
        <div className="impact-stat">
          <div className="big">{data.ley_30_1992.direct_live_citers.toLocaleString()}</div>
          <div className="lbl">Direct references removed</div>
        </div>
      </div>
      <div className="context-note">{data.interpretation}</div>
      <div style={{ marginTop: 10 }}>
        <EvidenceButton onClick={onEvidence} />
      </div>
    </div>
  );
}

export function Ley30RecommendationExtra({
  norm,
}: {
  norm: {
    priority?: string;
    priority_reason?: string;
    suggested_replacement_label?: string;
    dead_law_citations_count?: number;
    can_be_fully_cleaned_by_ley30_cleanup?: boolean;
  };
}): ReactNode {
  return (
    <>
      {norm.dead_law_citations_count != null && (
        <div className="meta-row">
          <span className="k">Dead-law cites</span>
          <span>{norm.dead_law_citations_count}</span>
        </div>
      )}
      {norm.can_be_fully_cleaned_by_ley30_cleanup != null && (
        <div className="meta-row">
          <span className="k">Fully cleaned?</span>
          <span>{norm.can_be_fully_cleaned_by_ley30_cleanup ? "Yes" : "No"}</span>
        </div>
      )}
      {norm.suggested_replacement_label && (
        <div className="meta-row">
          <span className="k">Suggested replacement</span>
          <span style={{ textAlign: "right" }}>{norm.suggested_replacement_label}</span>
        </div>
      )}
    </>
  );
}
