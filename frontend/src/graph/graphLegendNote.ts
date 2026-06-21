import type { GraphData } from "../types";

/** Contextual note when the graph shows a capped subgraph (not every edge). */
export function graphLegendNote(briefingKey: string, meta: GraphData["meta"]): string | undefined {
  if (!meta?.truncated || !meta.total_edges_available) return undefined;
  const shown = meta.edge_count ?? 0;
  const total = meta.total_edges_available;
  const cap = meta.max_edges_per_hub ?? 30;

  switch (briefingKey) {
    case "unreadable-laws":
      return `Graph preview: up to ${cap} amending norms drawn per ranked target (${shown} of ${total} AMENDS edges). The table counts distinct amending norms per target; ${total} includes repeat amendments by the same norm (multiple BOE events).`;
    case "omnibus-laws":
      return `Graph preview: up to ${cap} amended targets drawn per ranked omnibus norm (${shown} of ${total} AMENDS edges). The table counts distinct targets per omnibus norm; ${total} includes repeat amendment events to the same target.`;
    case "dead-law-dependencies":
      return `Graph preview: up to ${cap} live citers per ghost norm (${shown} of ${total} CITES edges drawn). Ghost rankings with live-citer counts are in the table above — not every citing norm.`;
    case "ley-30-1992-blast-radius":
      return `Graph preview: up to ${cap} citers drawn (${shown} of ${total} CITES edges). Every live direct citer is listed in the worklist table above; use pagination or CSV for the full set.`;
    default:
      return `Graph preview: ${shown} of ${total} connections shown (up to ${cap} per hub).`;
  }
}
