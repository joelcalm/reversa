import type { Collection, Core, CollectionArgument, NodeSingular } from "cytoscape";

export type GraphLayoutMode = "briefing-incoming" | "briefing-outgoing" | "auto";

/** Apply a layout tuned for hub-and-spoke briefing subgraphs. */
export function runBriefingLayout(cy: Core, mode: GraphLayoutMode): void {
  const hubs = cy.nodes('[is_hub = true]');
  const hubCount = hubs.length;

  if (hubCount > 0) {
    cy.layout({
      name: "concentric",
      fit: false,
      padding: 48,
      startAngle: (3 / 2) * Math.PI,
      sweep: 2 * Math.PI,
      clockwise: true,
      equidistant: false,
      minNodeSpacing: 36,
      avoidOverlap: true,
      concentric: (node: NodeSingular) => {
        if (node.data("is_hub")) return 1000;
        if (mode === "briefing-incoming") return node.indegree(false);
        if (mode === "briefing-outgoing") return node.outdegree(false);
        return node.degree(false);
      },
      levelWidth: () => 1,
    }).run();
  } else {
    cy.layout({
      name: "cose",
      fit: false,
      padding: 48,
      animate: false,
      nodeRepulsion: 9000,
      idealEdgeLength: 120,
      edgeElasticity: 0.45,
      nestingFactor: 0.1,
      gravity: 0.25,
      numIter: 1200,
    }).run();
  }

  fitGraph(cy, hubs.length ? hubs : cy.nodes());
}

/** Radial ego layout: focus at centre, incoming on the left arc, outgoing on the right. */
export function runExplorerLayout(cy: Core, focusId?: string): void {
  if (!focusId) {
    runFallbackCose(cy);
    return;
  }

  const focus = cy.getElementById(focusId);
  if (focus.empty()) {
    runFallbackCose(cy);
    return;
  }

  focus.addClass("focus");
  cy.nodes().not(focus).addClass("peripheral");

  const preds = focus.predecessors("node").not(focus);
  const succs = focus.successors("node").not(focus);

  const predIds = new Set(preds.map((n) => n.id()));
  const succIds = new Set(succs.map((n) => n.id()));

  const inOnly = preds.filter((n) => !succIds.has(n.id()));
  const outOnly = succs.filter((n) => !predIds.has(n.id()));
  const both = preds.filter((n) => succIds.has(n.id()));

  const inRadius = Math.max(200, inOnly.length * 16);
  const outRadius = Math.max(200, outOnly.length * 16);
  const bothRadius = Math.max(160, both.length * 22);

  placeOnArc(inOnly, 0, 0, inRadius, Math.PI * 0.58, Math.PI * 1.42);
  placeOnArc(outOnly, 0, 0, outRadius, -Math.PI * 0.42, Math.PI * 0.42);
  placeOnArc(both, 0, 0, bothRadius, Math.PI * 1.12, Math.PI * 1.88);

  focus.position({ x: 0, y: 0 });
  fitGraph(cy, cy.nodes());
}

function placeOnArc(
  nodes: Collection,
  cx: number,
  cy: number,
  radius: number,
  startAngle: number,
  endAngle: number,
): void {
  const n = nodes.length;
  if (n === 0) return;
  nodes.forEach((node, i) => {
    const t = n === 1 ? 0.5 : i / (n - 1);
    const angle = startAngle + (endAngle - startAngle) * t;
    node.position({
      x: cx + radius * Math.cos(angle),
      y: cy + radius * Math.sin(angle),
    });
  });
}

function runFallbackCose(cy: Core): void {
  cy.layout({
    name: "cose",
    fit: false,
    padding: 48,
    animate: false,
    nodeRepulsion: 12000,
    idealEdgeLength: 140,
    edgeElasticity: 0.45,
    nestingFactor: 0.1,
    gravity: 0.15,
    numIter: 1200,
  }).run();
  fitGraph(cy, cy.nodes());
}

function fitGraph(cy: Core, collection: CollectionArgument): void {
  if (collection.nonempty()) {
    cy.fit(collection, 72);
  } else {
    cy.fit(undefined, 72);
  }
  const z = cy.zoom();
  cy.minZoom(Math.min(0.12, z * 0.55));
  cy.maxZoom(3.5);
}

export function layoutModeForBriefing(briefingKey?: string): GraphLayoutMode {
  switch (briefingKey) {
    case "unreadable-laws":
    case "dead-law-dependencies":
    case "ley-30-1992-blast-radius":
      return "briefing-incoming";
    case "omnibus-laws":
      return "briefing-outgoing";
    default:
      return "auto";
  }
}
