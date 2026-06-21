import { useEffect, useState } from "react";
import { Copy, ExternalLink, X } from "lucide-react";
import { api } from "../api/client";
import type { BriefingKey, EvidenceResponse } from "../types";
import { formatBoeDate, StatusPill } from "./common";
import { ErrorView, Loading } from "./States";

export interface EvidenceTarget {
  briefingKey: BriefingKey;
  normId?: string;
  title?: string;
}

interface Props {
  target: EvidenceTarget | null;
  scope?: string;
  onClose: () => void;
}

const PAGE_SIZE = 25;

const EXPLANATION: Record<BriefingKey, string> = {
  "unreadable-laws":
    "This ranking comes from these graph edges: every distinct norm that AMENDS the selected norm.",
  "omnibus-laws":
    "This ranking comes from these graph edges: every distinct norm AMENDED by the selected act.",
  "dead-law-dependencies":
    "This number comes from these graph edges: live, in-scope norms that CITE the selected dead norm.",
  "ley-30-1992-blast-radius":
    "This number comes from these graph edges: live, in-scope norms that directly CITE Ley 30/1992.",
};

function CopyId({ id }: { id: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      type="button"
      className="copy-id"
      title="Copy BOE ID"
      onClick={() => {
        navigator.clipboard?.writeText(id).then(
          () => {
            setCopied(true);
            setTimeout(() => setCopied(false), 1200);
          },
          () => undefined,
        );
      }}
    >
      <Copy size={12} /> {copied ? "Copied" : id}
    </button>
  );
}

export default function EvidenceDrawer({ target, scope = "state", onClose }: Props) {
  const [data, setData] = useState<EvidenceResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [offset, setOffset] = useState(0);

  useEffect(() => {
    setOffset(0);
  }, [target?.briefingKey, target?.normId]);

  useEffect(() => {
    if (!target) return;
    let cancelled = false;
    setLoading(true);
    setError(null);
    api
      .evidence(target.briefingKey, { normId: target.normId, scope, limit: PAGE_SIZE, offset })
      .then((d) => !cancelled && setData(d))
      .catch((e: Error) => !cancelled && setError(e.message))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [target, scope, offset]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  if (!target) return null;

  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;
  const page = Math.floor(offset / PAGE_SIZE) + 1;

  return (
    <div className="drawer-overlay" onClick={onClose}>
      <aside className="drawer" onClick={(e) => e.stopPropagation()} role="dialog" aria-label="Evidence">
        <div className="drawer-header">
          <div>
            <div className="drawer-eyebrow">Evidence · raw BOE relations</div>
            <h3>{target.title ?? target.normId ?? "Evidence"}</h3>
          </div>
          <button type="button" className="graph-tool-btn" onClick={onClose} title="Close">
            <X size={16} />
          </button>
        </div>

        <p className="drawer-explain">{EXPLANATION[target.briefingKey]}</p>

        {loading && <Loading message="Loading evidence…" />}
        {error && <ErrorView message={error} />}

        {data && !loading && (
          <>
            <div className="drawer-count">
              {data.total.toLocaleString()} underlying relation{data.total === 1 ? "" : "s"}
            </div>
            <div className="evidence-list">
              {data.items.map((it, i) => (
                <div key={i} className="evidence-item">
                  <div className="evidence-rel">
                    <span className={`pill rel-${it.relation.relation_type}`}>
                      {it.relation.relation_type}
                    </span>
                    <span className="muted evidence-raw">
                      {it.relation.relation_label_raw ?? "—"}
                      {it.relation.relation_detail_raw
                        ? ` · ${it.relation.relation_detail_raw}`
                        : ""}
                    </span>
                  </div>
                  <div className="evidence-edge">
                    <div className="evidence-node">
                      <div className="evidence-node-title" title={it.source_norm.title}>
                        {it.source_norm.title ?? it.source_norm.id}
                      </div>
                      <div className="evidence-node-meta">
                        <CopyId id={it.source_norm.id} />
                        <StatusPill status={it.source_norm.lifecycle_status} />
                        {it.source_norm.url_html && (
                          <a href={it.source_norm.url_html} target="_blank" rel="noreferrer" title="Open in BOE">
                            <ExternalLink size={12} />
                          </a>
                        )}
                      </div>
                    </div>
                    <div className="evidence-arrow">→</div>
                    <div className="evidence-node">
                      <div className="evidence-node-title" title={it.target_norm.title}>
                        {it.target_norm.title ?? it.target_norm.id}
                      </div>
                      <div className="evidence-node-meta">
                        <CopyId id={it.target_norm.id} />
                        <StatusPill status={it.target_norm.lifecycle_status} />
                        {it.target_norm.url_html && (
                          <a href={it.target_norm.url_html} target="_blank" rel="noreferrer" title="Open in BOE">
                            <ExternalLink size={12} />
                          </a>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="muted evidence-pub">
                    Published {formatBoeDate(it.source_norm.publication_date)} ·{" "}
                    {it.source_norm.rank ?? "—"} · {it.source_norm.department ?? "—"}
                  </div>
                </div>
              ))}
            </div>

            {data.total > PAGE_SIZE && (
              <div className="table-pagination">
                <span className="muted">
                  Page {page} of {totalPages}
                </span>
                <div className="pagination-controls">
                  <button
                    type="button"
                    className="graph-tool-btn"
                    disabled={offset <= 0}
                    onClick={() => setOffset((o) => Math.max(0, o - PAGE_SIZE))}
                  >
                    Previous
                  </button>
                  <button
                    type="button"
                    className="graph-tool-btn"
                    disabled={page >= totalPages}
                    onClick={() => setOffset((o) => o + PAGE_SIZE)}
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </aside>
    </div>
  );
}
