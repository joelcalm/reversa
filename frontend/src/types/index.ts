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
  department_diversity?: number;
  omnibus_score?: number;
}
export interface GhostNorm extends Norm {
  live_citers: number;
}

export type ReplacementSuggestion = "LEY_39_2015" | "LEY_40_2015" | "LEGAL_REVIEW";
export type Confidence = "high" | "medium" | "low";
export type Priority = "High" | "Medium" | "Low";

export interface CitingNorm extends Norm {
  relation_label_raw?: string;
  relation_detail_raw?: string;
  dead_law_citations_count?: number;
  can_be_fully_cleaned_by_ley30_cleanup?: boolean;
  suggested_replacement?: ReplacementSuggestion;
  suggested_replacement_label?: string;
  suggested_replacement_confidence?: Confidence;
  suggested_replacement_reason?: string;
  matched_keywords?: { ley_39_2015: string[]; ley_40_2015: string[] };
  priority?: Priority;
  priority_reason?: string;
}

export interface RepealingNorm {
  id: string;
  title?: string;
  publication_date?: string;
  relation_label_raw?: string;
  relation_detail_raw?: string;
  url_html?: string;
  is_full_repeal?: boolean;
}
export interface ReplacementNorm {
  id: string;
  title?: string;
  role: string;
  url_html?: string;
  present_in_graph?: boolean;
}
export interface RepealContext {
  target_id: string;
  status: LifecycleStatus;
  title?: string;
  url_html?: string;
  boe_raw_repeal_date?: string | null;
  effective_repeal_date?: string | null;
  repealing_norms: RepealingNorm[];
  replacement_norms: ReplacementNorm[];
  display_note: string;
}

export interface CleanupImpact {
  briefing: string;
  scope: string;
  denominator_live_norms: number;
  before: { live_norms_citing_dead_law: number; percentage: number };
  ley_30_1992: {
    direct_live_citers: number;
    target_id: string;
    repeal_context: RepealContext;
  };
  after_simulated_cleanup: {
    live_norms_still_citing_dead_law: number;
    percentage: number;
    fully_cleaned_norms: number;
    remaining_dirty_norms: number;
  };
  interpretation: string;
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
  repeal_context?: RepealContext;
  total_live_direct_citers: number;
  citing_norms: CitingNorm[];
}

export type BriefingKey =
  | "unreadable-laws"
  | "omnibus-laws"
  | "dead-law-dependencies"
  | "ley-30-1992-blast-radius";

export interface EvidenceNorm {
  id: string;
  title?: string;
  rank?: string;
  department?: string;
  publication_date?: string;
  lifecycle_status?: LifecycleStatus;
  url_html?: string;
}
export interface EvidenceItem {
  source_norm: EvidenceNorm;
  target_norm: EvidenceNorm;
  relation: {
    relation_type: RelationType;
    relation_code?: string;
    relation_label_raw?: string;
    relation_detail_raw?: string;
    api_direction?: string;
    current_norm_id?: string;
  };
}
export interface EvidenceResponse {
  briefing: string;
  scope: string;
  norm_id: string;
  total: number;
  limit: number;
  offset: number;
  items: EvidenceItem[];
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
    replacement?: string;
    department?: string;
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
    filtered_from?: number;
    incoming_total?: number;
    outgoing_total?: number;
    edges_deduplicated?: number;
    direction?: string;
    limit?: number;
  };
}

export interface DataQuality extends Summary {
  unknown_target_relations: number;
  other_label_occurrences: number;
  distinct_raw_labels: number;
  labels: { label: string; normalized_type: string; count: number }[];
  label_limit: number;
}

export interface NormList {
  total: number;
  limit: number;
  offset: number;
  items: Norm[];
}
