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
};

export const graphStylesheet: StylesheetStyle[] = [
  {
    selector: "node",
    style: {
      "background-color": C.unknown,
      "border-color": C.unknownBorder,
      "border-width": 2,
      label: "data(label)",
      color: C.label,
      "font-size": "9px",
      "text-valign": "bottom",
      "text-halign": "center",
      "text-margin-y": 4,
      "text-max-width": "90px",
      "text-wrap": "ellipsis",
      width: 26,
      height: 26,
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
      "border-width": 4,
      "border-color": "#154d32",
      width: 38,
      height: 38,
      "font-size": "11px",
      "font-weight": "bold",
    },
  },
  {
    selector: "node:selected",
    style: { "border-width": 4, "border-color": "#154d32" },
  },
  {
    selector: "edge",
    style: {
      width: 1.6,
      "line-color": C.other,
      "target-arrow-color": C.other,
      "target-arrow-shape": "triangle",
      "arrow-scale": 0.9,
      "curve-style": "bezier",
      opacity: 0.85,
    },
  },
  {
    selector: 'edge[relation_type = "AMENDS"]',
    style: { "line-color": C.amends, "target-arrow-color": C.amends },
  },
  {
    selector: 'edge[relation_type = "CITES"]',
    style: { "line-color": C.cites, "target-arrow-color": C.cites },
  },
  {
    selector: 'edge[relation_type = "REPEALS"]',
    style: { "line-color": C.repeals, "target-arrow-color": C.repeals },
  },
];
