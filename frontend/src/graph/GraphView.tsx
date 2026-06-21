import { useCallback, useEffect, useRef, useState } from "react";
import cytoscape from "cytoscape";
import type { GraphData } from "../types";
import { graphStylesheet } from "./graphStyle";
import {
  layoutModeForBriefing,
  runBriefingLayout,
  runExplorerLayout,
  type GraphLayoutMode,
} from "./graphLayout";

interface Props {
  data: GraphData;
  focusId?: string;
  height?: number;
  briefingKey?: string;
  layoutMode?: GraphLayoutMode | "explorer";
  onNodeClick?: (id: string) => void;
}

export function GraphLegend({ note }: { note?: string }) {
  return (
    <div className="legend">
      <div className="legend-items">
        <span className="item">
          <span className="swatch" style={{ background: "#2e9e68" }} /> Live norm
        </span>
        <span className="item">
          <span className="swatch" style={{ background: "#b4453a" }} /> Repealed / annulled / expired
        </span>
        <span className="item">
          <span className="swatch hub" /> Hub (centre of subgraph)
        </span>
        <span className="item">
          <span className="swatch line" style={{ background: "#d98324" }} /> AMENDS
        </span>
        <span className="item">
          <span className="swatch line" style={{ background: "#2f6fb0" }} /> CITES
        </span>
        <span className="item">
          <span className="swatch line" style={{ background: "#b4453a" }} /> REPEALS
        </span>
      </div>
      {note && <span className="legend-note">{note}</span>}
    </div>
  );
}

function GraphToolbar({ cy }: { cy: cytoscape.Core | null }) {
  if (!cy) return null;
  const zoomIn = () => cy.zoom({ level: cy.zoom() * 1.25, renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 } });
  const zoomOut = () => cy.zoom({ level: cy.zoom() / 1.25, renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 } });
  const fit = () => {
    const hubs = cy.nodes('[is_hub = true]');
    cy.fit(hubs.length ? hubs : cy.nodes(), 72);
  };
  return (
    <div className="graph-toolbar">
      <button type="button" className="graph-tool-btn" onClick={zoomIn} title="Zoom in">
        +
      </button>
      <button type="button" className="graph-tool-btn" onClick={zoomOut} title="Zoom out">
        −
      </button>
      <button type="button" className="graph-tool-btn" onClick={fit} title="Fit to view">
        Fit
      </button>
    </div>
  );
}

export default function GraphView({
  data,
  focusId,
  height = 560,
  briefingKey,
  layoutMode,
  onNodeClick,
}: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);
  const [cyReady, setCyReady] = useState<cytoscape.Core | null>(null);
  const onNodeClickRef = useRef(onNodeClick);
  onNodeClickRef.current = onNodeClick;

  const initGraph = useCallback(() => {
    if (!containerRef.current) return;
    const cy = cytoscape({
      container: containerRef.current,
      elements: {
        nodes: data.nodes.map((n) => ({ data: { ...n.data } })),
        edges: data.edges.map((e) => ({ data: { ...e.data } })),
      },
      style: graphStylesheet,
      wheelSensitivity: 0.18,
      minZoom: 0.1,
      maxZoom: 3.5,
      boxSelectionEnabled: false,
    });

    if (layoutMode === "explorer" || !briefingKey) {
      runExplorerLayout(cy);
    } else {
      const mode = layoutMode ?? layoutModeForBriefing(briefingKey);
      runBriefingLayout(cy, mode);
    }

    if (focusId) {
      const focus = cy.getElementById(focusId);
      focus.addClass("focus");
      cy.fit(focus.closedNeighborhood().nodes(), 80);
    }

    cy.on("tap", "node", (evt) => {
      const node = evt.target;
      cy.nodes().removeClass("dimmed");
      cy.edges().removeClass("highlighted");
      const hood = node.closedNeighborhood();
      cy.elements().not(hood).nodes().addClass("dimmed");
      hood.edges().addClass("highlighted");
      onNodeClickRef.current?.(node.id());
    });

    cyRef.current = cy;
    setCyReady(cy);
    return cy;
  }, [data, focusId, briefingKey, layoutMode]);

  useEffect(() => {
    const cy = initGraph();
    return () => {
      cy?.destroy();
      cyRef.current = null;
      setCyReady(null);
    };
  }, [initGraph]);

  // Resize when the container changes (e.g. window resize).
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const ro = new ResizeObserver(() => {
      cyRef.current?.resize();
      const hubs = cyRef.current?.nodes('[is_hub = true]');
      if (hubs && hubs.length) cyRef.current?.fit(hubs, 72);
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  return (
    <div className="graph-viewport" style={{ height }}>
      <GraphToolbar cy={cyReady} />
      <div ref={containerRef} className="graph-canvas" />
    </div>
  );
}
