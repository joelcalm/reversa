import { BRIEFING_ANCHORS, BRIEFING_KEYS } from "../../briefings/keys";
import type { BriefingKey } from "../../types";

const LABELS: Record<string, string> = {
  "unreadable-laws": "1",
  "omnibus-laws": "2",
  "dead-law-dependencies": "3",
  "ley-30-1992-blast-radius": "4",
};

export default function RoomAnchorNav() {
  return (
    <nav className="room-anchor-nav" aria-label="Briefing sections">
      <a href="#overview" className="anchor-link">
        Overview
      </a>
      {BRIEFING_KEYS.map((key: BriefingKey) => (
        <a key={key} href={`#${BRIEFING_ANCHORS[key]}`} className="anchor-link">
          {LABELS[key]}
        </a>
      ))}
    </nav>
  );
}
