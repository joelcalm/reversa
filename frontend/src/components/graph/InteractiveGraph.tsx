import { useMemo, useState } from "react";
import GraphView, { GraphLegend } from "../../graph/GraphView";
import type { GraphData, LifecycleStatus, RelationType } from "../../types";
import { Empty, ErrorView, Loading } from "../States";

export interface GraphFilters {
  search: string;
  lifecycle: string;
  relationType: string;
  rank: string;
  department: string;
}

interface Props {
  data: GraphData | null;
  loading?: boolean;
  error?: string | null;
  focusId?: string;
  briefingKey?: string;
  height?: number;
  legendNote?: string;
  onNodeClick?: (id: string) => void;
  showFilterBar?: boolean;
}

const DEFAULT_FILTERS: GraphFilters = {
  search: "",
  lifecycle: "",
  relationType: "",
  rank: "",
  department: "",
};

function filterGraph(data: GraphData, filters: GraphFilters, focusId?: string): GraphData {
  const q = filters.search.trim().toLowerCase();
  const nodeOk = (n: GraphData["nodes"][0]) => {
    const d = n.data;
    if (filters.lifecycle && d.lifecycle_status !== filters.lifecycle) return false;
    if (filters.rank && d.rank !== filters.rank) return false;
    if (filters.department && (d as { department?: string }).department !== filters.department)
      return false;
    if (q) {
      const hay = `${d.id} ${d.label ?? ""} ${d.title ?? ""}`.toLowerCase();
      if (!hay.includes(q)) return false;
    }
    return true;
  };

  const visibleIds = new Set(
    data.nodes.filter(nodeOk).map((n) => n.data.id)
  );
  // Always keep focus hub visible
  const hubId = focusId ?? data.meta?.focus_id;
  if (hubId) visibleIds.add(hubId);

  const edges = data.edges.filter((e) => {
    const d = e.data;
    if (filters.relationType && d.relation_type !== filters.relationType) return false;
    return visibleIds.has(d.source) && visibleIds.has(d.target);
  });

  const connected = new Set<string>();
  for (const e of edges) {
    connected.add(e.data.source);
    connected.add(e.data.target);
  }
  const nodes = data.nodes.filter(
    (n) => visibleIds.has(n.data.id) && (connected.has(n.data.id) || n.data.id === hubId)
  );

  return {
    nodes,
    edges,
    meta: {
      ...data.meta,
      node_count: nodes.length,
      edge_count: edges.length,
      filtered_from: data.nodes.length,
    },
  };
}

export default function InteractiveGraph({
  data,
  loading,
  error,
  focusId,
  briefingKey,
  height = 520,
  legendNote,
  onNodeClick,
  showFilterBar = true,
}: Props) {
  const [filters, setFilters] = useState<GraphFilters>(DEFAULT_FILTERS);
  const [layoutKey, setLayoutKey] = useState(0);

  const ranks = useMemo(() => {
    if (!data) return [];
    return Array.from(new Set(data.nodes.map((n) => n.data.rank).filter(Boolean))).sort();
  }, [data]);

  const departments = useMemo(() => {
    if (!data) return [];
    return Array.from(
      new Set(
        data.nodes
          .map((n) => (n.data as { department?: string }).department)
          .filter(Boolean)
      )
    ).sort() as string[];
  }, [data]);

  const filtered = useMemo(() => {
    if (!data) return null;
    return filterGraph(data, filters, focusId);
  }, [data, filters, focusId]);

  const note = useMemo(() => {
    const parts: string[] = [];
    if (filtered?.meta?.filtered_from && filtered.meta.filtered_from > (filtered.nodes.length ?? 0)) {
      parts.push(`Showing ${filtered.nodes.length} of ${filtered.meta.filtered_from} nodes`);
    }
    if (data?.meta?.truncated) {
      parts.push(
        `Graph capped at ${data.meta.edge_count} of ${data.meta.total_edges_available ?? "?"} edges`
      );
    }
    if (legendNote) parts.push(legendNote);
    return parts.length ? parts.join(". ") + "." : undefined;
  }, [filtered, data, legendNote]);

  return (
    <div className="interactive-graph">
      {showFilterBar && data && (
        <div className="graph-filters">
          <input
            className="input"
            placeholder="Search nodes in graph…"
            value={filters.search}
            onChange={(e) => setFilters((f) => ({ ...f, search: e.target.value }))}
          />
          <select
            className="input"
            value={filters.lifecycle}
            onChange={(e) => setFilters((f) => ({ ...f, lifecycle: e.target.value }))}
          >
            <option value="">All statuses</option>
            {(["LIVE", "REPEALED", "ANNULLED", "EXPIRED"] as LifecycleStatus[]).map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
          <select
            className="input"
            value={filters.relationType}
            onChange={(e) => setFilters((f) => ({ ...f, relationType: e.target.value }))}
          >
            <option value="">All relations</option>
            {(["AMENDS", "CITES", "REPEALS", "OTHER"] as RelationType[]).map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
          {ranks.length > 0 && (
            <select
              className="input"
              value={filters.rank}
              onChange={(e) => setFilters((f) => ({ ...f, rank: e.target.value }))}
            >
              <option value="">All ranks</option>
              {ranks.map((r) => (
                <option key={r} value={r}>{r}</option>
              ))}
            </select>
          )}
          {departments.length > 0 && (
            <select
              className="input"
              value={filters.department}
              onChange={(e) => setFilters((f) => ({ ...f, department: e.target.value }))}
            >
              <option value="">All departments</option>
              {departments.map((d) => (
                <option key={d} value={d}>{d}</option>
              ))}
            </select>
          )}
        </div>
      )}

      <div className="graph-shell">
        {loading && <Loading message="Building subgraph…" />}
        {error && <ErrorView message={error} />}
        {!loading && !error && filtered && filtered.nodes.length === 0 && (
          <Empty message="No nodes match the current filters." />
        )}
        {!loading && !error && filtered && filtered.nodes.length > 0 && (
          <>
            <GraphView
              data={filtered}
              focusId={focusId}
              briefingKey={briefingKey}
              height={height}
              onNodeClick={onNodeClick}
              onResetLayout={() => setLayoutKey((k) => k + 1)}
              layoutKey={layoutKey}
            />
            <GraphLegend note={note} />
          </>
        )}
      </div>
    </div>
  );
}
