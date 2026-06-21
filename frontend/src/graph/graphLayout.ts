import type { Core, CollectionArgument, NodeSingular } from "cytoscape";

export type GraphLayoutMode = "briefing-incoming" | "briefing-outgoing" | "auto";

/** Apply a layout tuned for hub-and-spoke briefing subgraphs. */
export function runBriefingLayout(cy: Core, mode: GraphLayoutMode): void {
  const hubs = cy.nodes('[is_hub = true]');
  const hubCount = hubs.length;

  if (hubCount > 0) {
    // Concentric: hubs in the centre, amenders/citers in outer rings.
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
        // Incoming: leaf amenders on the outside; outgoing: amended norms outside.
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

export function runExplorerLayout(cy: Core): void {
  cy.layout({
    name: "cose",
    fit: false,
    padding: 48,
    animate: false,
    nodeRepulsion: 7000,
    idealEdgeLength: 100,
    edgeElasticity: 0.45,
    nestingFactor: 0.1,
    gravity: 0.3,
    numIter: 1000,
  }).run();
  fitGraph(cy, cy.nodes());
}

function fitGraph(cy: Core, collection: CollectionArgument): void {
  if (collection.nonempty()) {
    cy.fit(collection, 72);
  } else {
    cy.fit(undefined, 72);
  }
  // Don't let the user zoom out so far that the graph becomes a hairline.
  const z = cy.zoom();
  cy.minZoom(Math.min(0.15, z * 0.55));
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
