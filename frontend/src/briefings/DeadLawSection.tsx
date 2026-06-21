import { useMemo, useState } from "react";
import { api } from "../api/client";
import BriefingBody, { useDefaultSelection } from "../components/briefing/BriefingBody";
import BriefingHeader from "../components/briefing/BriefingHeader";
import BriefingSection from "../components/briefing/BriefingSection";
import RecommendationPanel from "../components/briefing/RecommendationPanel";
import InteractiveGraph from "../components/graph/InteractiveGraph";
import { BoeLink, EvidenceButton, formatBoeDate, KpiCard, NormTitle, StatusPill } from "../components/common";
import EvidenceDrawer, { type EvidenceTarget } from "../components/EvidenceDrawer";
import { Column, SortableTable } from "../components/SortableTable";
import { ErrorView, Loading } from "../components/States";
import { useFetch } from "../components/useFetch";
import { BRIEFING_ANCHORS } from "../briefings/keys";
import { useNeighborhoodGraph } from "../hooks/useNeighborhoodGraph";
import type { GhostNorm } from "../types";
import { recommendGhost } from "../utils/recommendations";

interface Props {
  focusMode?: boolean;
}

export default function DeadLawSection({ focusMode }: Props) {
  const { data, loading, error } = useFetch(() => api.deadLaw("state", 5), []);
  const [selectedId, setSelectedId] = useDefaultSelection(data?.top_ghost_norms);
  const [evidence, setEvidence] = useState<EvidenceTarget | null>(null);

  const selected = useMemo(
    () => data?.top_ghost_norms.find((i) => i.id === selectedId) ?? data?.top_ghost_norms[0],
    [data, selectedId],
  );

  const selectedRank = useMemo(() => {
    if (!data || !selected) return 1;
    return data.top_ghost_norms.findIndex((g) => g.id === selected.id) + 1;
  }, [data, selected]);

  const { data: graphData, loading: graphLoading, error: graphError } = useNeighborhoodGraph({
    normId: selected?.id ?? null,
    relationType: "CITES",
    direction: "incoming",
    limit: 120,
  });

  const top = data?.top_ghost_norms[0];
  const openEvidence = (id: string, title?: string) =>
    setEvidence({ briefingKey: "dead-law-dependencies", normId: id, title: title ?? id });

  const columns: Column<GhostNorm>[] = [
    { key: "rank", label: "#", render: (r) => <span className="rank-badge">{r.rank_position}</span> },
    { key: "id", label: "BOE ID", render: (r) => <BoeLink norm={r} />, sortValue: (r) => r.id },
    { key: "title", label: "Title (ghost norm)", render: (r) => <NormTitle norm={r} />, sortValue: (r) => r.title ?? "" },
    { key: "status", label: "Status", render: (r) => <StatusPill status={r.lifecycle_status} />, sortValue: (r) => r.lifecycle_status ?? "" },
    { key: "repeal", label: "Repeal date", render: (r) => formatBoeDate(r.repeal_date), sortValue: (r) => r.repeal_date ?? "" },
    {
      key: "citers",
      label: "Live citers",
      numeric: true,
      render: (r) => r.live_citers,
      sortValue: (r) => r.live_citers,
    },
    {
      key: "evidence",
      label: "Evidence",
      render: (r) => <EvidenceButton onClick={() => openEvidence(r.id, r.title)} />,
    },
  ];

  const chips = (data?.top_ghost_norms ?? []).map((i, idx) => ({
    id: i.id,
    label: `#${idx + 1} · ${i.live_citers} citers`,
  }));

  return (
    <BriefingSection id={BRIEFING_ANCHORS["dead-law-dependencies"]}>
      {loading && <Loading />}
      {error && <ErrorView message={error} />}
      {data && top && (
        <>
          <BriefingHeader
            number={3}
            title="Dead-law dependencies"
            question="How much of the live statute book still cites repealed norms?"
            headline={`${data.percentage}%`}
            answer={`${data.live_norms_citing_repealed_count.toLocaleString()} of ${data.live_norms_count.toLocaleString()} live norms cite at least one repealed norm. Top ghost: ${top.title?.split(",")[0] ?? top.id} (${top.live_citers} live citers).`}
            scopeNote="Scope: state-level norms · CITES edges only"
            briefingKey="dead-law-dependencies"
            focusMode={focusMode}
            onViewEvidence={() => openEvidence(top.id, top.title)}
          >
            {focusMode && (
              <div className="kpi-grid briefing-kpis">
                <KpiCard value={`${data.percentage}%`} label="Live norms citing dead law" />
                <KpiCard
                  value={data.live_norms_citing_repealed_count.toLocaleString()}
                  label="Numerator"
                />
                <KpiCard value={data.live_norms_count.toLocaleString()} label="Denominator" />
              </div>
            )}
          </BriefingHeader>
          <BriefingBody
            chips={chips}
            selectedId={selectedId}
            onSelect={setSelectedId}
            showTable={focusMode}
            graph={
              <InteractiveGraph
                data={graphData}
                loading={graphLoading}
                error={graphError}
                focusId={selected?.id}
                briefingKey="dead-law-dependencies"
                legendNote="Incoming CITES from live norms to the selected ghost"
                onNodeClick={(id) => {
                  setSelectedId(id);
                  openEvidence(id);
                }}
              />
            }
            panel={
              <RecommendationPanel
                norm={selected}
                recommendation={selected ? recommendGhost(selected, selectedRank) : null}
                extra={
                  selected && (
                    <div className="meta-row">
                      <span className="k">Live citers</span>
                      <span>{selected.live_citers}</span>
                    </div>
                  )
                }
              />
            }
            table={
              <>
                <div className="section-title">Top ghost norms — repealed norms most cited by live norms</div>
                {data.top_ghost_norms.length > 0 ? (
                  <SortableTable
                    columns={columns}
                    rows={data.top_ghost_norms}
                    initialSort="citers"
                    onRowClick={(r) => setSelectedId(r.id)}
                    selectedId={selectedId}
                    rowId={(r) => r.id}
                  />
                ) : (
                  <div className="card card-pad muted">No live norms cite repealed norms in this scope.</div>
                )}
              </>
            }
          />
        </>
      )}
      <EvidenceDrawer target={evidence} scope="state" onClose={() => setEvidence(null)} />
    </BriefingSection>
  );
}
