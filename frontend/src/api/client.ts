import type {
  BlastRadiusBriefing,
  DeadLawBriefing,
  GraphData,
  Norm,
  NormList,
  OmnibusBriefing,
  Summary,
  UnreadableBriefing,
} from "../types";

// Same-origin relative base; Vite proxies /api to the backend in dev.
const BASE = "";

async function getJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`HTTP ${res.status} for ${path}: ${text.slice(0, 200)}`);
  }
  return (await res.json()) as T;
}

export const api = {
  summary: () => getJSON<Summary>("/api/summary"),

  unreadable: (scope = "state", limit = 5) =>
    getJSON<UnreadableBriefing>(`/api/briefings/unreadable-laws?scope=${scope}&limit=${limit}`),
  omnibus: (scope = "state", limit = 5) =>
    getJSON<OmnibusBriefing>(`/api/briefings/omnibus-laws?scope=${scope}&limit=${limit}`),
  deadLaw: (scope = "state", limit = 5) =>
    getJSON<DeadLawBriefing>(`/api/briefings/dead-law-dependencies?scope=${scope}&limit=${limit}`),
  blastRadius: (scope = "state") =>
    getJSON<BlastRadiusBriefing>(`/api/briefings/ley-30-1992-blast-radius?scope=${scope}`),

  briefingGraph: (key: string, scope = "state") =>
    getJSON<GraphData>(`/api/graph/briefing/${key}?scope=${scope}`),

  norms: (params: {
    search?: string;
    status?: string;
    rank?: string;
    scope?: string;
    limit?: number;
    offset?: number;
  }) => {
    const q = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== "") q.set(k, String(v));
    });
    return getJSON<NormList>(`/api/norms?${q.toString()}`);
  },

  norm: (id: string) => getJSON<Norm>(`/api/norms/${encodeURIComponent(id)}`),

  neighborhood: (
    id: string,
    opts?: { relationType?: string; direction?: string; limit?: number },
  ) => {
    const q = new URLSearchParams({ limit: String(opts?.limit ?? 80) });
    if (opts?.relationType) q.set("relation_type", opts.relationType);
    if (opts?.direction && opts.direction !== "all") q.set("direction", opts.direction);
    return getJSON<GraphData>(`/api/norms/${encodeURIComponent(id)}/neighborhood?${q.toString()}`);
  },
};
