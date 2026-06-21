import { useEffect, useRef } from "react";
import cytoscape from "cytoscape";
import dagre from "cytoscape-dagre";
import type { GraphData } from "../types";
import { graphStylesheet } from "./graphStyle";

cytoscape.use(dagre);

interface Props {
  data: GraphData;
  focusId?: string;
  height?: number;
  onNodeClick?: (id: string) => void;
}

export function GraphLegend() {
  return (
    <div className="legend">
      <span className="item">
        <span className="swatch" style={{ background: "#2e9e68" }} /> Live norm
      </span>
      <span className="item">
        <span className="swatch" style={{ background: "#b4453a" }} /> Repealed / annulled / expired
      </span>
      <span className="item">
        <span className="swatch" style={{ background: "#c2ccc6" }} /> Unknown (not ingested)
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
  );
}

export default function GraphView({ data, focusId, height = 460, onNodeClick }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    const cy = cytoscape({
      container: containerRef.current,
      elements: {
        nodes: data.nodes.map((n) => ({ data: { ...n.data } })),
        edges: data.edges.map((e) => ({ data: { ...e.data } })),
      },
      style: graphStylesheet,
      layout: {
        name: "dagre",
        // @ts-expect-error dagre layout options are untyped
        rankDir: "LR",
        nodeSep: 28,
        rankSep: 70,
        animate: false,
      },
      wheelSensitivity: 0.2,
      minZoom: 0.2,
      maxZoom: 2.5,
    });

    if (focusId) {
      cy.getElementById(focusId).addClass("focus");
    }
    if (onNodeClick) {
      cy.on("tap", "node", (evt) => onNodeClick(evt.target.id()));
    }
    cy.fit(undefined, 30);
    cyRef.current = cy;

    return () => {
      cy.destroy();
      cyRef.current = null;
    };
  }, [data, focusId, onNodeClick]);

  return <div ref={containerRef} className="graph-canvas" style={{ height }} />;
}
