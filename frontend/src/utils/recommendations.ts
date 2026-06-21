import type {
  GhostNorm,
  OmnibusItem,
  UnreadableItem,
} from "../types";

export interface Recommendation {
  label: string;
  reason: string;
}

const HIGH_IMPACT_RANKS = new Set([
  "ley",
  "ley orgánica",
  "ley organica",
  "real decreto legislativo",
  "real decreto-ley",
  "real decreto ley",
]);

function isHighImpactRank(rank?: string): boolean {
  return HIGH_IMPACT_RANKS.has((rank ?? "").trim().toLowerCase());
}

function isBudgetLaw(title?: string): boolean {
  const t = (title ?? "").toLowerCase();
  return t.includes("presupuesto") || t.includes("presupuestos generales");
}

export function recommendUnreadable(item: UnreadableItem, topItems: UnreadableItem[]): Recommendation {
  if (item.lifecycle_status && item.lifecycle_status !== "LIVE") {
    return {
      label: "Historical / lower priority",
      reason: `Status is ${item.lifecycle_status}; consolidation is less urgent than for live norms.`,
    };
  }
  const maxCount = Math.max(...topItems.map((i) => i.amending_count), 1);
  if (isHighImpactRank(item.rank) && item.amending_count >= maxCount * 0.5) {
    return {
      label: "High rewrite priority",
      reason: `${item.amending_count} distinct amending norms on a high-impact ${item.rank ?? "norm"} — prioritize for consolidation or rewrite.`,
    };
  }
  return {
    label: "Monitor",
    reason: "Among the top amended norms but lower immediate rewrite pressure than the highest-ranked live norms.",
  };
}

export function recommendOmnibus(item: OmnibusItem): Recommendation {
  if (isBudgetLaw(item.title)) {
    return {
      label: "Budget-law exception / review separately",
      reason: "Budget laws are expected to affect many areas; still relevant as an omnibus pattern but review context differs.",
    };
  }
  const diversity = item.subject_diversity ?? 0;
  if (item.target_count >= 50 && diversity >= 30) {
    return {
      label: "Retrospective omnibus review",
      reason: `Amended ${item.target_count} norms across ${diversity} subject areas — strong candidate for retrospective impact review.`,
    };
  }
  if (item.target_count >= 30 && diversity >= 15) {
    return {
      label: "High omnibus pattern",
      reason: `Touches ${item.target_count} norms with subject diversity ${diversity} — review as a legislative-quality control example.`,
    };
  }
  return {
    label: "Monitor",
    reason: "Lower omnibus breadth among the current top-ranked acts.",
  };
}

export function recommendGhost(item: GhostNorm, rank: number): Recommendation {
  if (rank <= 2 || item.live_citers >= 100) {
    return {
      label: "Wave 1 cleanup",
      reason: `${item.live_citers} live norms still cite this repealed norm — highest simplification leverage.`,
    };
  }
  if (item.live_citers >= 50) {
    return {
      label: "High leverage ghost",
      reason: `${item.live_citers} live citers — significant dead-law contamination.`,
    };
  }
  return {
    label: "Later wave",
    reason: "Lower live-citer count; address after the highest-leverage ghost norms.",
  };
}
