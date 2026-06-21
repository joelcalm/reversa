import { useMemo, useState } from "react";
import { api } from "../api/client";
import BriefingBody, { useDefaultSelection } from "../components/briefing/BriefingBody";
import BriefingHeader from "../components/briefing/BriefingHeader";
import BriefingSection from "../components/briefing/BriefingSection";
import RecommendationPanel from "../components/briefing/RecommendationPanel";
import InteractiveGraph from "../components/graph/InteractiveGraph";
import { BoeLink, EvidenceButton, formatBoeDate, NormTitle, StatusPill } from "../components/common";
import EvidenceDrawer, { type EvidenceTarget } from "../components/EvidenceDrawer";
import { Column, SortableTable } from "../components/SortableTable";
import { ErrorView, Loading } from "../components/States";
import { useFetch } from "../components/useFetch";
import { BRIEFING_ANCHORS } from "../briefings/keys";
import { useNeighborhoodGraph } from "../hooks/useNeighborhoodGraph";
import type { UnreadableItem } from "../types";
import { recommendUnreadable } from "../utils/recommendations";

interface Props {
  focusMode?: boolean;
}

export default function UnreadableSection({ focusMode }: Props) {
  const { data, loading, error } = useFetch(() => api.unreadable("state", 5), []);
  const [selectedId, setSelectedId] = useDefaultSelection(data?.items);
  const [evidence, setEvidence] = useState<EvidenceTarget | null>(null);

  const selected = useMemo(
    () => data?.items.find((i) => i.id === selectedId) ?? data?.items[0],
    [data, selectedId],
  );

  const { data: graphData, loading: graphLoading, error: graphError } = useNeighborhoodGraph({
    normId: selected?.id ?? null,
    relationType: "AMENDS",
    direction: "incoming",
    limit: 120,
  });

  const top = data?.items[0];
  const openEvidence = (id: string, title?: string) =>
    setEvidence({ briefingKey: "unreadable-laws", normId: id, title: title ?? id });

  const columns: Column<UnreadableItem>[] = [
    { key: "rank", label: "#", render: (r) => <span className="rank-badge">{r.rank_position}</span> },
    { key: "id", label: "BOE ID", render: (r) => <BoeLink norm={r} />, sortValue: (r) => r.id },
    { key: "title", label: "Title", render: (r) => <NormTitle norm={r} />, sortValue: (r) => r.title ?? "" },
    { key: "rankName", label: "Rank", render: (r) => r.rank ?? "—", sortValue: (r) => r.rank ?? "" },
    { key: "dept", label: "Department", render: (r) => r.department ?? "—", sortValue: (r) => r.department ?? "" },
    { key: "pub", label: "Published", render: (r) => formatBoeDate(r.publication_date), sortValue: (r) => r.publication_date ?? "" },
    { key: "status", label: "Status", render: (r) => <StatusPill status={r.lifecycle_status} />, sortValue: (r) => r.lifecycle_status ?? "" },
    {
      key: "count",
      label: "Distinct amending norms",
      numeric: true,
      render: (r) => r.amending_count,
      sortValue: (r) => r.amending_count,
    },
    {
      key: "evidence",
      label: "Evidence",
      render: (r) => <EvidenceButton onClick={() => openEvidence(r.id, r.title)} />,
    },
  ];

  const chips = (data?.items ?? []).map((i, idx) => ({
    id: i.id,
    label: `#${idx + 1} · ${i.amending_count} amenders`,
  }));

  return (
    <BriefingSection id={BRIEFING_ANCHORS["unreadable-laws"]}>
      {loading && <Loading />}
      {error && <ErrorView message={error} />}
      {data && top && (
        <>
          <BriefingHeader
            number={1}
            title="Unreadable laws"
            question="Which norms are hardest to read because they were amended so many times?"
            headline={top.amending_count}
            answer={`${top.title?.split(",")[0] ?? top.id} has been amended by ${top.amending_count} distinct norms — the highest in scope.`}
            scopeNote="Scope: state-level norms"
            briefingKey="unreadable-laws"
            focusMode={focusMode}
            onViewEvidence={() => openEvidence(top.id, top.title)}
          />
          <BriefingBody
            chips={chips}
            selectedId={selectedId}
            onSelect={setSelectedId}
            graph={
              <InteractiveGraph
                data={graphData}
                loading={graphLoading}
                error={graphError}
                focusId={selected?.id}
                briefingKey="unreadable-laws"
                onNodeClick={(id) => {
                  setSelectedId(id);
                  if (data.items.some((i) => i.id === id)) openEvidence(id);
                }}
              />
            }
            panel={
              <RecommendationPanel
                norm={selected}
                recommendation={selected ? recommendUnreadable(selected, data.items) : null}
                extra={
                  selected && (
                    <div className="meta-row">
                      <span className="k">Amending norms</span>
                      <span>{selected.amending_count}</span>
                    </div>
                  )
                }
              />
            }
            table={
              <>
                <div className="section-title">Rankings — top 5 norms most amended by others</div>
                <SortableTable
                  columns={columns}
                  rows={data.items}
                  initialSort="count"
                  onRowClick={(r) => setSelectedId(r.id)}
                  selectedId={selectedId}
                  rowId={(r) => r.id}
                />
              </>
            }
          />
        </>
      )}
      <EvidenceDrawer target={evidence} scope="state" onClose={() => setEvidence(null)} />
    </BriefingSection>
  );
}
