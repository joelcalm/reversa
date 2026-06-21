import { useCallback, useEffect, useMemo } from "react";
import { api } from "../api/client";
import OverviewHero from "../components/briefing/OverviewHero";
import RoomAnchorNav from "../components/briefing/RoomAnchorNav";
import { useFetch } from "../components/useFetch";
import DeadLawSection from "../briefings/DeadLawSection";
import Ley30Section from "../briefings/Ley30Section";
import OmnibusSection from "../briefings/OmnibusSection";
import UnreadableSection from "../briefings/UnreadableSection";
import { BRIEFING_ANCHORS } from "../briefings/keys";
import type { OverviewInsights } from "../components/briefing/overviewTypes";

const FIRST_BRIEFING_ANCHOR = BRIEFING_ANCHORS["unreadable-laws"];

export default function BriefingRoom() {
  const { data: summary, loading: summaryLoading, error: summaryError } = useFetch(
    () => api.summary(),
    [],
  );
  const { data: unreadable } = useFetch(() => api.unreadable("state", 5), []);
  const { data: omnibus } = useFetch(() => api.omnibus("state", 5), []);
  const { data: deadLaw } = useFetch(() => api.deadLaw("state", 5), []);
  const { data: blast } = useFetch(() => api.blastRadius("state"), []);

  const insights: OverviewInsights | null = useMemo(() => {
    if (!unreadable?.items[0] || !omnibus?.items[0] || !deadLaw || !blast) return null;
    return {
      cards: [
        {
          anchor: BRIEFING_ANCHORS["unreadable-laws"],
          title: "Unreadable laws",
          mainNumber: String(unreadable.items[0].amending_count),
          subtitle: `Top: ${unreadable.items[0].title?.split(",")[0] ?? unreadable.items[0].id}`,
          actionLabel: "Review rewrite priorities",
        },
        {
          anchor: BRIEFING_ANCHORS["omnibus-laws"],
          title: "Omnibus laws",
          mainNumber: String(omnibus.items[0].target_count),
          subtitle: `Top: ${omnibus.items[0].title?.split(",")[0] ?? omnibus.items[0].id}`,
          actionLabel: "Inspect omnibus patterns",
        },
        {
          anchor: BRIEFING_ANCHORS["dead-law-dependencies"],
          title: "Dead-law dependencies",
          mainNumber: `${deadLaw.percentage}%`,
          subtitle: `${deadLaw.live_norms_citing_repealed_count.toLocaleString()} live norms cite dead law`,
          actionLabel: "Plan cleanup waves",
        },
        {
          anchor: BRIEFING_ANCHORS["ley-30-1992-blast-radius"],
          title: "Ley 30/1992 blast radius",
          mainNumber: String(blast.total_live_direct_citers),
          subtitle: "Live norms still citing the repealed law",
          actionLabel: "Open cleanup worklist",
        },
      ],
    };
  }, [unreadable, omnibus, deadLaw, blast]);

  const startCouncilBriefing = useCallback(() => {
    const el = document.getElementById(FIRST_BRIEFING_ANCHOR);
    if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
  }, []);

  useEffect(() => {
    const hash = window.location.hash.replace(/^#/, "");
    if (hash) {
      const el = document.getElementById(hash);
      if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, []);

  const insightsLoading = !insights && (!!unreadable || !!omnibus || !!deadLaw || !!blast);

  return (
    <div className="briefing-room">
      <RoomAnchorNav />
      <OverviewHero
        summary={summary}
        insights={insights}
        loading={summaryLoading || insightsLoading}
        error={summaryError}
        onStartBriefing={startCouncilBriefing}
      />
      <UnreadableSection />
      <OmnibusSection />
      <DeadLawSection />
      <Ley30Section />
    </div>
  );
}
