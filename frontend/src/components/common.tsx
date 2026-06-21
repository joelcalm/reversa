import type { ReactNode } from "react";
import type { LifecycleStatus, Norm } from "../types";

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
