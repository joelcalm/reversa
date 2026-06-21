import type { ReactNode } from "react";
import { Info, Search } from "lucide-react";
import type { Confidence, LifecycleStatus, Norm, Priority, ReplacementSuggestion } from "../types";

export function StatusPill({ status }: { status?: LifecycleStatus }) {
  const s = status ?? "UNKNOWN";
  return <span className={`pill ${s}`}>{s}</span>;
}

export function formatBoeDate(d?: string): string {
  if (!d) return "—";
  // BOE dates are YYYYMMDD.
  const m = /^(\d{4})(\d{2})(\d{2})$/.exec(d);
  if (m) return `${m[3]}/${m[2]}/${m[1]}`;
  return d;
}

export function BoeLink({ norm }: { norm: Norm }) {
  const url = norm.url_html;
  if (!url) return <span className="muted">{norm.id}</span>;
  return (
    <a href={url} target="_blank" rel="noreferrer" title="Open in BOE">
      {norm.id}
    </a>
  );
}

export function NormTitle({ norm }: { norm: Norm }) {
  return <span title={norm.title}>{norm.title ?? norm.id}</span>;
}

export function KpiCard({ value, label }: { value: ReactNode; label: string }) {
  return (
    <div className="card kpi">
      <div className="kpi-value">{value}</div>
      <div className="kpi-label">{label}</div>
    </div>
  );
}

export function EvidenceButton({ onClick }: { onClick: () => void }) {
  return (
    <button type="button" className="evidence-btn" onClick={onClick} title="Trace this number back to BOE relations">
      <Search size={13} /> View evidence
    </button>
  );
}

export function InfoTip({ text }: { text: ReactNode }) {
  return (
    <span className="info-tip" tabIndex={0}>
      <Info size={14} />
      <span className="info-bubble">{text}</span>
    </span>
  );
}

const REPLACEMENT_LABELS: Record<ReplacementSuggestion, string> = {
  LEY_39_2015: "Ley 39/2015",
  LEY_40_2015: "Ley 40/2015",
  LEGAL_REVIEW: "Needs legal review",
};

export function ReplacementChip({
  suggestion,
  label,
}: {
  suggestion?: ReplacementSuggestion;
  label?: string;
}) {
  if (!suggestion) return <span className="muted">—</span>;
  const cls =
    suggestion === "LEY_39_2015" ? "repl-39" : suggestion === "LEY_40_2015" ? "repl-40" : "repl-review";
  return <span className={`chip ${cls}`}>{label ?? REPLACEMENT_LABELS[suggestion]}</span>;
}

export function ConfidenceChip({ confidence }: { confidence?: Confidence }) {
  if (!confidence) return <span className="muted">—</span>;
  return <span className={`chip conf-${confidence}`}>{confidence}</span>;
}

export function PriorityChip({ priority }: { priority?: Priority }) {
  if (!priority) return <span className="muted">—</span>;
  return <span className={`chip prio-${priority}`}>{priority}</span>;
}
