export type LifecycleStatus = "LIVE" | "REPEALED" | "ANNULLED" | "EXPIRED" | "UNKNOWN";
export type RelationType = "AMENDS" | "REPEALS" | "CITES" | "OTHER";

export interface Norm {
  id: string;
  title?: string;
  official_number?: string;
  rank?: string;
  rank_code?: string;
  scope?: string;
  department?: string;
  publication_date?: string;
  disposition_date?: string;
  effective_date?: string;
  repeal_date?: string;
  annulment_date?: string;
  lifecycle_status?: LifecycleStatus;
  is_live?: boolean;
  is_repealed?: boolean;
  url_eli?: string;
  url_html?: string;
  rank_position?: number;
  metrics?: Record<string, number>;
}

export interface Summary {
  total_norms: number;
  total_relations: number;
  relation_counts_by_type: Record<string, number>;
  lifecycle_counts: Record<string, number>;
  default_scope: string;
  scope_label: string;
  last_ingestion_at?: string | null;
}

export interface UnreadableItem extends Norm {
  amending_count: number;
}
export interface OmnibusItem extends Norm {
  target_count: number;
  subject_diversity?: number;
}
export interface GhostNorm extends Norm {
  live_citers: number;
}
export interface CitingNorm extends Norm {
  relation_label_raw?: string;
  relation_detail_raw?: string;
}

export interface UnreadableBriefing {
  briefing: string;
  scope: string;
  items: UnreadableItem[];
}
export interface OmnibusBriefing {
  briefing: string;
  scope: string;
  items: OmnibusItem[];
}
export interface DeadLawBriefing {
  briefing: string;
  scope: string;
  live_norms_count: number;
  live_norms_citing_repealed_count: number;
  percentage: number;
  top_ghost_norms: GhostNorm[];
}
export interface BlastRadiusBriefing {
  briefing: string;
  scope: string;
  target_id: string;
  ley_30_1992?: Norm;
  total_live_direct_citers: number;
  citing_norms: CitingNorm[];
}

export interface CyNode {
  data: {
    id: string;
    label: string;
    title?: string;
    lifecycle_status?: LifecycleStatus;
    rank?: string;
    url_html?: string;
    is_live?: boolean | null;
    is_hub?: boolean;
    metrics?: Record<string, number | boolean>;
  };
}
export interface CyEdge {
  data: {
    id: string;
    source: string;
    target: string;
    relation_type: RelationType;
    relation_label_raw?: string;
    relation_detail_raw?: string;
  };
}
export interface GraphData {
  nodes: CyNode[];
  edges: CyEdge[];
  meta?: {
    node_count?: number;
    edge_count?: number;
    truncated?: boolean;
    max_edges_per_hub?: number;
    total_edges_available?: number;
    focus_id?: string;
    incoming_total?: number;
    outgoing_total?: number;
    edges_deduplicated?: number;
    direction?: string;
    limit?: number;
  };
}

export interface NormList {
  total: number;
  limit: number;
  offset: number;
  items: Norm[];
}
