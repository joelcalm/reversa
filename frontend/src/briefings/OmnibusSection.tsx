import { useMemo, useState } from "react";
import { api } from "../api/client";
import BriefingBody, { useDefaultSelection } from "../components/briefing/BriefingBody";
import BriefingHeader from "../components/briefing/BriefingHeader";
import BriefingSection from "../components/briefing/BriefingSection";
import RecommendationPanel from "../components/briefing/RecommendationPanel";
import InteractiveGraph from "../components/graph/InteractiveGraph";
import { BoeLink, EvidenceButton, formatBoeDate, InfoTip, NormTitle } from "../components/common";
import EvidenceDrawer, { type EvidenceTarget } from "../components/EvidenceDrawer";
import { Column, SortableTable } from "../components/SortableTable";
import { ErrorView, Loading } from "../components/States";
import { useFetch } from "../components/useFetch";
import { BRIEFING_ANCHORS } from "../briefings/keys";
import { useNeighborhoodGraph } from "../hooks/useNeighborhoodGraph";
import type { OmnibusItem } from "../types";
import { recommendOmnibus } from "../utils/recommendations";

interface Props {
  focusMode?: boolean;
}

export default function OmnibusSection({ focusMode }: Props) {
  const { data, loading, error } = useFetch(() => api.omnibus("state", 5), []);
  const [selectedId, setSelectedId] = useDefaultSelection(data?.items);
  const [evidence, setEvidence] = useState<EvidenceTarget | null>(null);

  const selected = useMemo(
    () => data?.items.find((i) => i.id === selectedId) ?? data?.items[0],
    [data, selectedId],
  );

  const { data: graphData, loading: graphLoading, error: graphError } = useNeighborhoodGraph({
    normId: selected?.id ?? null,
    relationType: "AMENDS",
    direction: "outgoing",
    limit: 120,
  });

  const top = data?.items[0];
  const openEvidence = (id: string, title?: string) =>
    setEvidence({ briefingKey: "omnibus-laws", normId: id, title: title ?? id });

  const hasDeptDiversity = !!data?.items.some((i) => i.department_diversity !== undefined);
  const hasScore = !!data?.items.some((i) => i.omnibus_score !== undefined);

  const columns: Column<OmnibusItem>[] = [
    { key: "rank", label: "#", render: (r) => <span className="rank-badge">{r.rank_position}</span> },
    { key: "id", label: "BOE ID", render: (r) => <BoeLink norm={r} />, sortValue: (r) => r.id },
    { key: "title", label: "Title", render: (r) => <NormTitle norm={r} />, sortValue: (r) => r.title ?? "" },
    { key: "rankName", label: "Rank", render: (r) => r.rank ?? "—", sortValue: (r) => r.rank ?? "" },
    { key: "dept", label: "Department", render: (r) => r.department ?? "—", sortValue: (r) => r.department ?? "" },
    { key: "pub", label: "Published", render: (r) => formatBoeDate(r.publication_date), sortValue: (r) => r.publication_date ?? "" },
    {
      key: "diversity",
      label: "Subject diversity",
      numeric: true,
      render: (r) => r.subject_diversity ?? 0,
      sortValue: (r) => r.subject_diversity ?? 0,
    },
    ...(hasDeptDiversity
      ? [
          {
            key: "deptdiv",
            label: "Dept. diversity",
            numeric: true,
            render: (r: OmnibusItem) => r.department_diversity ?? 0,
            sortValue: (r: OmnibusItem) => r.department_diversity ?? 0,
          },
        ]
      : []),
    ...(hasScore
      ? [
          {
            key: "score",
            label: "Secondary score",
            numeric: true,
            render: (r: OmnibusItem) => r.omnibus_score ?? 0,
            sortValue: (r: OmnibusItem) => r.omnibus_score ?? 0,
          },
        ]
      : []),
    {
      key: "count",
      label: "Norms amended",
      numeric: true,
      render: (r) => r.target_count,
      sortValue: (r) => r.target_count,
    },
    {
      key: "evidence",
      label: "Evidence",
      render: (r) => <EvidenceButton onClick={() => openEvidence(r.id, r.title)} />,
    },
  ];

  const chips = (data?.items ?? []).map((i, idx) => ({
    id: i.id,
    label: `#${idx + 1} · ${i.target_count} targets`,
  }));

  return (
    <BriefingSection id={BRIEFING_ANCHORS["omnibus-laws"]}>
      {loading && <Loading />}
      {error && <ErrorView message={error} />}
      {data && top && (
        <>
          <BriefingHeader
            number={2}
            title="Omnibus laws"
            question="Which single acts amended the most other norms?"
            headline={top.target_count}
            answer={`${top.title?.split(",")[0] ?? top.id} amended ${top.target_count} distinct norms — the broadest omnibus pattern in scope.`}
            scopeNote="Scope: state-level norms"
            briefingKey="omnibus-laws"
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
                briefingKey="omnibus-laws"
                onNodeClick={(id) => {
                  setSelectedId(id);
                  if (data.items.some((i) => i.id === id)) openEvidence(id);
                }}
              />
            }
            panel={
              <RecommendationPanel
                norm={selected}
                recommendation={selected ? recommendOmnibus(selected) : null}
                extra={
                  selected && (
                    <>
                      <div className="meta-row">
                        <span className="k">Norms amended</span>
                        <span>{selected.target_count}</span>
                      </div>
                      <div className="meta-row">
                        <span className="k">
                          Subject diversity{" "}
                          <InfoTip text="Distinct BOE subject tags among norms amended by this act." />
                        </span>
                        <span>{selected.subject_diversity ?? "—"}</span>
                      </div>
                      {selected.department_diversity != null && (
                        <div className="meta-row">
                          <span className="k">Dept. diversity</span>
                          <span>{selected.department_diversity}</span>
                        </div>
                      )}
                      {selected.omnibus_score != null && (
                        <div className="meta-row">
                          <span className="k">Secondary score</span>
                          <span>{selected.omnibus_score}</span>
                        </div>
                      )}
                    </>
                  )
                }
              />
            }
            table={
              <>
                <div className="section-title">
                  Rankings — top 5 omnibus norms{" "}
                  <InfoTip
                    text={
                      <>
                        Ranking is by distinct amended norms. Subject diversity counts distinct BOE
                        subject tags among targets. The omnibus score is a secondary indicator only.
                      </>
                    }
                  />
                </div>
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
