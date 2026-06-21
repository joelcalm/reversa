import type { BriefingKey } from "../types";

export const BRIEFING_KEYS: BriefingKey[] = [
  "unreadable-laws",
  "omnibus-laws",
  "dead-law-dependencies",
  "ley-30-1992-blast-radius",
];

export const BRIEFING_ANCHORS: Record<BriefingKey, string> = {
  "unreadable-laws": "briefing-unreadable",
  "omnibus-laws": "briefing-omnibus",
  "dead-law-dependencies": "briefing-dead-law",
  "ley-30-1992-blast-radius": "briefing-ley-30-1992",
};

export const BRIEFING_ROUTE_SLUG: Record<BriefingKey, string> = {
  "unreadable-laws": "unreadable-laws",
  "omnibus-laws": "omnibus-laws",
  "dead-law-dependencies": "dead-law",
  "ley-30-1992-blast-radius": "ley-30-1992",
};

export function keyFromSlug(slug: string): BriefingKey | null {
  const entry = Object.entries(BRIEFING_ROUTE_SLUG).find(([, s]) => s === slug);
  return entry ? (entry[0] as BriefingKey) : null;
}
