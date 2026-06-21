import { api } from "../api/client";
import GraphView, { GraphLegend } from "../graph/GraphView";
import { graphLegendNote } from "../graph/graphLegendNote";
import { useFetch } from "./useFetch";
import { Empty, ErrorView, Loading } from "./States";

interface Props {
  briefingKey: string;
  scope?: string;
  focusId?: string;
  onNodeClick?: (id: string) => void;
}

export default function BriefingGraph({ briefingKey, scope = "state", focusId, onNodeClick }: Props) {
  const { data, loading, error } = useFetch(() => api.briefingGraph(briefingKey, scope), [
    briefingKey,
    scope,
  ]);

  const legendNote = data ? graphLegendNote(briefingKey, data.meta) : undefined;

  return (
    <div className="graph-shell">
      {loading && <Loading message="Building subgraph…" />}
      {error && <ErrorView message={error} />}
      {!loading && !error && data && data.nodes.length === 0 && (
        <Empty message="No edges in this subgraph for the current scope." />
      )}
      {!loading && !error && data && data.nodes.length > 0 && (
        <>
          <GraphView
            data={data}
            briefingKey={briefingKey}
            focusId={focusId}
            onNodeClick={onNodeClick}
            height={560}
          />
          <GraphLegend note={legendNote} />
        </>
      )}
    </div>
  );
}
