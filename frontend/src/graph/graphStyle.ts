import type { StylesheetStyle } from "cytoscape";

// Colors mirror the CSS variables in theme.css so the graph matches the UI.
const C = {
  live: "#2e9e68",
  liveBorder: "#1f6b46",
  dead: "#b4453a",
  deadBorder: "#8c352c",
  unknown: "#c2ccc6",
  unknownBorder: "#9aa6a0",
  label: "#1a2421",
  amends: "#d98324",
  cites: "#2f6fb0",
  repeals: "#b4453a",
  other: "#9aa6a0",
  hubRing: "#154d32",
};

const FONT = "Satoshi, system-ui, sans-serif";

export const graphStylesheet: StylesheetStyle[] = [
  {
    selector: "node",
    style: {
      "background-color": C.unknown,
      "border-color": C.unknownBorder,
      "border-width": 2,
      label: "data(label)",
      color: C.label,
      "font-family": FONT,
      "font-size": "11px",
      "font-weight": 500,
      "text-valign": "bottom",
      "text-halign": "center",
      "text-margin-y": 6,
      "text-max-width": "110px",
      "text-wrap": "ellipsis",
      "text-background-color": "#ffffff",
      "text-background-opacity": 0.92,
      "text-background-padding": "2px",
      "text-background-shape": "roundrectangle",
      width: 34,
      height: 34,
    },
  },
  {
    selector: "node[is_hub = true]",
    style: {
      width: 52,
      height: 52,
      "border-width": 4,
      "border-color": C.hubRing,
      "font-size": "12px",
      "font-weight": 700,
      "z-index": 10,
    },
  },
  {
    selector: 'node[lifecycle_status = "LIVE"]',
    style: { "background-color": C.live, "border-color": C.liveBorder },
  },
  {
    selector: 'node[lifecycle_status = "REPEALED"]',
    style: { "background-color": C.dead, "border-color": C.deadBorder },
  },
  {
    selector: 'node[lifecycle_status = "ANNULLED"]',
    style: { "background-color": C.dead, "border-color": C.deadBorder },
  },
  {
    selector: 'node[lifecycle_status = "EXPIRED"]',
    style: { "background-color": C.dead, "border-color": C.deadBorder },
  },
  {
    selector: "node.focus",
    style: {
      "border-width": 5,
      "border-color": "#0d3d28",
      width: 58,
      height: 58,
      "font-size": "13px",
      "font-weight": 700,
      "overlay-opacity": 0.08,
      "overlay-color": C.live,
    },
  },
  {
    selector: "node:selected",
    style: { "border-width": 5, "border-color": "#0d3d28" },
  },
  {
    selector: "edge",
    style: {
      width: 2,
      "line-color": C.other,
      "target-arrow-color": C.other,
      "target-arrow-shape": "triangle",
      "arrow-scale": 1,
      "curve-style": "unbundled-bezier",
      "control-point-distances": 40,
      "control-point-weights": 0.4,
      opacity: 0.75,
    },
  },
  {
    selector: 'edge[relation_type = "AMENDS"]',
    style: { "line-color": C.amends, "target-arrow-color": C.amends, width: 2.2 },
  },
  {
    selector: 'edge[relation_type = "CITES"]',
    style: { "line-color": C.cites, "target-arrow-color": C.cites, width: 2.2 },
  },
  {
    selector: 'edge[relation_type = "REPEALS"]',
    style: { "line-color": C.repeals, "target-arrow-color": C.repeals, width: 2.2 },
  },
  {
    selector: "edge.highlighted",
    style: { opacity: 1, width: 3 },
  },
  {
    selector: "node.dimmed",
    style: { opacity: 0.35 },
  },
];
