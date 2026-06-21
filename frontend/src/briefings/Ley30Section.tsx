import { useMemo, useState } from "react";
import { Download } from "lucide-react";
import { api } from "../api/client";
import BriefingBody, { useDefaultSelection } from "../components/briefing/BriefingBody";
import BriefingHeader from "../components/briefing/BriefingHeader";
import BriefingSection from "../components/briefing/BriefingSection";
import RecommendationPanel from "../components/briefing/RecommendationPanel";
import InteractiveGraph from "../components/graph/InteractiveGraph";
import {
  BoeLink,
  ConfidenceChip,
  EvidenceButton,
  formatBoeDate,
  KpiCard,
  NormTitle,
  PriorityChip,
  ReplacementChip,
  StatusPill,
} from "../components/common";
import EvidenceDrawer, { type EvidenceTarget } from "../components/EvidenceDrawer";
import { Column, SortableTable } from "../components/SortableTable";
import { ErrorView, Loading } from "../components/States";
import { useFetch } from "../components/useFetch";
import { BRIEFING_ANCHORS } from "../briefings/keys";
import {
  CleanupImpactCard,
  Ley30RecommendationExtra,
  RepealContextBlock,
} from "../briefings/ley30Blocks";
import { useNeighborhoodGraph } from "../hooks/useNeighborhoodGraph";
import type { CitingNorm, GraphData } from "../types";
import { downloadCsv, toCsv } from "../utils/csv";

const TARGET_ID = "BOE-A-1992-26318";

interface Props {
  focusMode?: boolean;
}

export default function Ley30Section({ focusMode }: Props) {
  const { data, loading, error } = useFetch(() => api.blastRadius("state"), []);
  const [selectedId, setSelectedId] = useDefaultSelection(data?.citing_norms);
  const [evidence, setEvidence] = useState<EvidenceTarget | null>(null);
  const [filter, setFilter] = useState("");
  const [replFilter, setReplFilter] = useState("");
  const [confFilter, setConfFilter] = useState("");
  const [prioFilter, setPrioFilter] = useState("");
  const [deptFilter, setDeptFilter] = useState("");
  const [rankFilter, setRankFilter] = useState("");

  const selected = useMemo(
    () => data?.citing_norms.find((i) => i.id === selectedId) ?? data?.citing_norms[0],
    [data, selectedId],
  );

  const replacementMap = useMemo(() => {
    const m = new Map<string, string>();
    for (const n of data?.citing_norms ?? []) {
      if (n.suggested_replacement) m.set(n.id, n.suggested_replacement);
    }
    return m;
  }, [data]);

  const { data: rawGraph, loading: graphLoading, error: graphError } = useNeighborhoodGraph({
    normId: data?.target_id ?? TARGET_ID,
    relationType: "CITES",
    direction: "incoming",
    limit: 200,
  });

  const graphData = useMemo((): GraphData | null => {
    if (!rawGraph) return null;
    return {
      ...rawGraph,
      nodes: rawGraph.nodes.map((n) => ({
        ...n,
        data: {
          ...n.data,
          replacement: replacementMap.get(n.data.id) ?? n.data.replacement,
        },
      })),
    };
  }, [rawGraph, replacementMap]);

  const openEvidence = (id: string, title?: string) =>
    setEvidence({
      briefingKey: "ley-30-1992-blast-radius",
      normId: id,
      title: title ?? id,
    });

  const departments = useMemo(
    () => Array.from(new Set((data?.citing_norms ?? []).map((n) => n.department).filter(Boolean))).sort(),
    [data],
  );
  const ranks = useMemo(
    () => Array.from(new Set((data?.citing_norms ?? []).map((n) => n.rank).filter(Boolean))).sort(),
    [data],
  );

  const filtered = useMemo(() => {
    if (!data) return [];
    const q = filter.trim().toLowerCase();
    return data.citing_norms.filter((n) => {
      if (
        q &&
        !(
          n.id.toLowerCase().includes(q) ||
          (n.title ?? "").toLowerCase().includes(q) ||
          (n.department ?? "").toLowerCase().includes(q)
        )
      )
        return false;
      if (replFilter && n.suggested_replacement !== replFilter) return false;
      if (confFilter && n.suggested_replacement_confidence !== confFilter) return false;
      if (prioFilter && n.priority !== prioFilter) return false;
      if (deptFilter && n.department !== deptFilter) return false;
      if (rankFilter && n.rank !== rankFilter) return false;
      return true;
    });
  }, [data, filter, replFilter, confFilter, prioFilter, deptFilter, rankFilter]);

  const columns: Column<CitingNorm>[] = [
    { key: "rank", label: "#", render: (r) => <span className="rank-badge">{r.rank_position}</span> },
    { key: "id", label: "BOE ID", render: (r) => <BoeLink norm={r} />, sortValue: (r) => r.id },
    { key: "title", label: "Title", render: (r) => <NormTitle norm={r} />, sortValue: (r) => r.title ?? "" },
    { key: "rankName", label: "Rank", render: (r) => r.rank ?? "—", sortValue: (r) => r.rank ?? "" },
    { key: "dept", label: "Department", render: (r) => r.department ?? "—", sortValue: (r) => r.department ?? "" },
    { key: "pub", label: "Published", render: (r) => formatBoeDate(r.publication_date), sortValue: (r) => r.publication_date ?? "" },
    {
      key: "deadcount",
      label: "Dead-law cites",
      numeric: true,
      render: (r) => r.dead_law_citations_count ?? "—",
      sortValue: (r) => r.dead_law_citations_count ?? 0,
    },
    {
      key: "fully",
      label: "Fully cleaned?",
      render: (r) => (r.can_be_fully_cleaned_by_ley30_cleanup ? "Yes" : "No"),
      sortValue: (r) => (r.can_be_fully_cleaned_by_ley30_cleanup ? 1 : 0),
    },
    {
      key: "repl",
      label: "Suggested replacement",
      render: (r) => (
        <span title={r.suggested_replacement_reason}>
          <ReplacementChip suggestion={r.suggested_replacement} label={r.suggested_replacement_label} />
        </span>
      ),
      sortValue: (r) => r.suggested_replacement ?? "",
    },
    {
      key: "conf",
      label: "Confidence",
      render: (r) => <ConfidenceChip confidence={r.suggested_replacement_confidence} />,
      sortValue: (r) => r.suggested_replacement_confidence ?? "",
    },
    {
      key: "prio",
      label: "Priority",
      render: (r) => (
        <span title={r.priority_reason}>
          <PriorityChip priority={r.priority} />
        </span>
      ),
      sortValue: (r) => r.priority ?? "",
    },
    {
      key: "evidence",
      label: "Evidence",
      render: (r) => <EvidenceButton onClick={() => openEvidence(r.id, r.title)} />,
    },
  ];

  const exportCsv = () => {
    if (!data) return;
    const csv = toCsv(
      [
        "rank", "boe_id", "title", "rank_name", "department", "published", "status",
        "relation_label_raw", "relation_detail_raw", "dead_law_citations_count",
        "can_be_fully_cleaned_by_ley30_cleanup", "suggested_replacement",
        "suggested_replacement_confidence", "suggested_replacement_reason",
        "matched_keywords_39", "matched_keywords_40", "priority", "priority_reason", "url",
      ],
      data.citing_norms.map((n) => [
        n.rank_position ?? "",
        n.id,
        n.title ?? "",
        n.rank ?? "",
        n.department ?? "",
        formatBoeDate(n.publication_date),
        n.lifecycle_status ?? "",
        n.relation_label_raw ?? "",
        n.relation_detail_raw ?? "",
        n.dead_law_citations_count ?? "",
        n.can_be_fully_cleaned_by_ley30_cleanup ? "yes" : "no",
        n.suggested_replacement ?? "",
        n.suggested_replacement_confidence ?? "",
        n.suggested_replacement_reason ?? "",
        (n.matched_keywords?.ley_39_2015 ?? []).join("; "),
        (n.matched_keywords?.ley_40_2015 ?? []).join("; "),
        n.priority ?? "",
        n.priority_reason ?? "",
        n.url_html ?? "",
      ]),
    );
    downloadCsv("ley-30-1992-worklist.csv", csv);
  };

  const total = data?.total_live_direct_citers ?? 0;
  const legendNote = data
    ? `Citers colored by suggested replacement heuristic. Full blast radius: ${total} live direct citers.`
    : undefined;

  const cleanupImpact = (
    <CleanupImpactCard
      scope="state"
      onEvidence={() => openEvidence(TARGET_ID, "Ley 30/1992 — live direct citers")}
    />
  );

  return (
    <BriefingSection id={BRIEFING_ANCHORS["ley-30-1992-blast-radius"]}>
      {loading && <Loading />}
      {error && <ErrorView message={error} />}
      {data && (
        <>
          <BriefingHeader
            number={4}
            title="The unfinished repeal: Ley 30/1992"
            question="How many live norms still cite a law repealed in 2015?"
            headline={total}
            answer={`${total} live norms still cite Ley 30/1992 directly — a repeal that remains unfinished in the statute book.`}
            scopeNote="Scope: state-level norms · CITES edges only"
            briefingKey="ley-30-1992-blast-radius"
            focusMode={focusMode}
            onViewEvidence={() =>
              openEvidence(TARGET_ID, data.ley_30_1992?.title ?? "Ley 30/1992")
            }
          >
            {focusMode && (
              <>
                <div className="kpi-grid briefing-kpis">
                  <KpiCard value={total} label="Live norms citing Ley 30/1992" />
                  <KpiCard
                    value={<StatusPill status={data.ley_30_1992?.lifecycle_status} />}
                    label="Status of Ley 30/1992"
                  />
                  <KpiCard
                    value={data.citing_norms.filter((n) => n.can_be_fully_cleaned_by_ley30_cleanup).length}
                    label="Fully cleanable by cleanup"
                  />
                  <KpiCard
                    value={data.citing_norms.filter((n) => n.priority === "High").length}
                    label="High-priority norms"
                  />
                </div>
                {data.repeal_context && <RepealContextBlock ctx={data.repeal_context} />}
                {cleanupImpact}
              </>
            )}
          </BriefingHeader>

          <BriefingBody
            chips={[]}
            selectedId={selectedId}
            onSelect={setSelectedId}
            showTable={focusMode}
            graph={
              <InteractiveGraph
                data={graphData}
                loading={graphLoading}
                error={graphError}
                focusId={data.target_id}
                briefingKey="ley-30-1992-blast-radius"
                legendNote={legendNote}
                height={560}
                onNodeClick={(id) => {
                  if (data.citing_norms.some((n) => n.id === id)) setSelectedId(id);
                  openEvidence(id);
                }}
              />
            }
            panel={
              <RecommendationPanel
                norm={selected}
                recommendation={
                  selected?.priority
                    ? { label: `${selected.priority} priority`, reason: selected.priority_reason ?? "" }
                    : null
                }
                extra={selected ? <Ley30RecommendationExtra norm={selected} /> : null}
              />
            }
            table={
              <>
                <div className="toolbar">
                  <input
                    className="input"
                    placeholder="Filter by id, title or department…"
                    value={filter}
                    onChange={(e) => setFilter(e.target.value)}
                    style={{ minWidth: 240, flex: 1 }}
                  />
                  <select className="input" value={replFilter} onChange={(e) => setReplFilter(e.target.value)}>
                    <option value="">All replacements</option>
                    <option value="LEY_39_2015">Ley 39/2015</option>
                    <option value="LEY_40_2015">Ley 40/2015</option>
                    <option value="LEGAL_REVIEW">Needs legal review</option>
                  </select>
                  <select className="input" value={confFilter} onChange={(e) => setConfFilter(e.target.value)}>
                    <option value="">All confidence</option>
                    <option value="high">High</option>
                    <option value="medium">Medium</option>
                    <option value="low">Low</option>
                  </select>
                  <select className="input" value={prioFilter} onChange={(e) => setPrioFilter(e.target.value)}>
                    <option value="">All priorities</option>
                    <option value="High">High</option>
                    <option value="Medium">Medium</option>
                    <option value="Low">Low</option>
                  </select>
                  <select className="input" value={deptFilter} onChange={(e) => setDeptFilter(e.target.value)}>
                    <option value="">All departments</option>
                    {departments.map((d) => (
                      <option key={d} value={d}>{d}</option>
                    ))}
                  </select>
                  <select className="input" value={rankFilter} onChange={(e) => setRankFilter(e.target.value)}>
                    <option value="">All ranks</option>
                    {ranks.map((r) => (
                      <option key={r} value={r}>{r}</option>
                    ))}
                  </select>
                  <button className="btn" onClick={exportCsv} disabled={!data.citing_norms.length}>
                    <Download size={16} /> Download CSV
                  </button>
                </div>
                <p className="muted" style={{ fontSize: 13 }}>
                  Suggested replacements are a deterministic heuristic for legal review, not a final legal conclusion.
                </p>
                <div className="section-title">
                  Cleanup worklist ({filtered.length} of {data.citing_norms.length})
                </div>
                {filtered.length > 0 ? (
                  <SortableTable
                    columns={columns}
                    rows={filtered}
                    initialSort="prio"
                    pageSize={20}
                    onRowClick={(r) => setSelectedId(r.id)}
                    selectedId={selectedId}
                    rowId={(r) => r.id}
                  />
                ) : (
                  <div className="card card-pad muted">No norms match the current filters.</div>
                )}
              </>
            }
          />

          {!focusMode && <div className="briefing-cleanup-below">{cleanupImpact}</div>}
        </>
      )}
      <EvidenceDrawer target={evidence} scope="state" onClose={() => setEvidence(null)} />
    </BriefingSection>
  );
}
