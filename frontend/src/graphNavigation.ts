import {
  type BreadcrumbItem,
  type FocusDepth,
  type GraphEdge,
  type GraphNode,
} from "./types";

/**
 * Compute the N-hop neighborhood around a center node using breadth-first search.
 * Traverses edges in both directions so that both upstream and downstream
 * dependencies within the hop radius are included.
 */
export function computeNeighborhood(
  nodes: GraphNode[],
  edges: GraphEdge[],
  centerNodeId: string,
  depth: FocusDepth,
): { nodes: GraphNode[]; edges: GraphEdge[] } {
  if (depth === "all") {
    return { nodes, edges };
  }

  const hopLimit = Number(depth);
  if (hopLimit <= 0) {
    const single = nodes.filter((node) => node.id === centerNodeId);
    return { nodes: single, edges: [] };
  }

  // Build adjacency map
  const adjacency = new Map<string, Set<string>>();
  for (const edge of edges) {
    if (!adjacency.has(edge.source)) adjacency.set(edge.source, new Set());
    if (!adjacency.has(edge.target)) adjacency.set(edge.target, new Set());
    adjacency.get(edge.source)!.add(edge.target);
    adjacency.get(edge.target)!.add(edge.source);
  }

  const visited = new Map<string, number>();
  const queue: Array<{ id: string; hop: number }> = [{ id: centerNodeId, hop: 0 }];
  visited.set(centerNodeId, 0);

  while (queue.length > 0) {
    const { id, hop } = queue.shift()!;
    if (hop >= hopLimit) continue;

    const neighbors = adjacency.get(id);
    if (!neighbors) continue;

    for (const neighborId of neighbors) {
      if (!visited.has(neighborId)) {
        visited.set(neighborId, hop + 1);
        queue.push({ id: neighborId, hop: hop + 1 });
      }
    }
  }

  const neighborhoodNodes = nodes.filter((node) => visited.has(node.id));
  const neighborhoodEdges = edges.filter(
    (edge) => visited.has(edge.source) && visited.has(edge.target),
  );

  return { nodes: neighborhoodNodes, edges: neighborhoodEdges };
}

/**
 * Check if a candidate node is contained within a package or module.
 */
function isDescendant(
  parent: GraphNode,
  candidate: GraphNode,
  edges: GraphEdge[],
): boolean {
  if (candidate.id === parent.id) return true;

  // Direct containment via edge
  const hasContainmentEdge = edges.some(
    (e) => e.source === parent.id && e.target === candidate.id && (e.type === "contains" || e.type === "defines"),
  );
  if (hasContainmentEdge) return true;

  // Path-based hierarchy check
  if (parent.path && candidate.path) {
    if (parent.type === "package") {
      const normalizedParent = parent.path.replace(/\\/g, "/").replace(/\/+$/, "");
      const normalizedCandidate = candidate.path.replace(/\\/g, "/");
      if (
        normalizedCandidate === normalizedParent ||
        normalizedCandidate.startsWith(`${normalizedParent}/`)
      ) {
        return true;
      }
    } else if (parent.type === "module") {
      const normalizedParent = parent.path.replace(/\\/g, "/");
      const normalizedCandidate = candidate.path.replace(/\\/g, "/");
      if (normalizedCandidate === normalizedParent) {
        return true;
      }
    }
  }

  // ID-based hierarchy check (e.g. "package:backend" -> "module:backend.analysis")
  if (parent.type === "package") {
    const pkgPrefix = parent.name.endsWith(".") ? parent.name : `${parent.name}.`;
    if (candidate.name.startsWith(pkgPrefix) || candidate.id.includes(`:${parent.name}.`)) {
      return true;
    }
  }

  return false;
}

/**
 * Filter nodes for drill-down into a package or module.
 */
export function filterDrillDown(
  nodes: GraphNode[],
  edges: GraphEdge[],
  drillNode: GraphNode | null,
): GraphNode[] {
  if (!drillNode) return nodes;

  // Find all children recursively
  const childIds = new Set<string>();
  childIds.add(drillNode.id);

  // Collect direct and indirect descendants
  for (const node of nodes) {
    if (isDescendant(drillNode, node, edges)) {
      childIds.add(node.id);
    }
  }

  // Also include nodes linked by 'contains' or 'defines' transitively
  let added = true;
  while (added) {
    added = false;
    for (const edge of edges) {
      if (childIds.has(edge.source) && (edge.type === "contains" || edge.type === "defines")) {
        if (!childIds.has(edge.target)) {
          childIds.add(edge.target);
          added = true;
        }
      }
    }
  }

  return nodes.filter((node) => childIds.has(node.id));
}

/**
 * Build breadcrumb navigation items for the current drill-down state.
 */
export function buildBreadcrumbs(
  drillNode: GraphNode | null,
  allNodes: GraphNode[],
  edges: GraphEdge[],
): BreadcrumbItem[] {
  const crumbs: BreadcrumbItem[] = [{ id: null, label: "All" }];
  if (!drillNode) return crumbs;

  // Check if drillNode has a parent package
  if (drillNode.type === "module") {
    // Find enclosing package by contains edge or path
    const parentEdge = edges.find(
      (e) => e.target === drillNode.id && e.type === "contains",
    );
    let parentPackage: GraphNode | undefined;
    if (parentEdge) {
      parentPackage = allNodes.find((n) => n.id === parentEdge.source && n.type === "package");
    }
    if (!parentPackage && drillNode.path) {
      const normalizedPath = drillNode.path.replace(/\\/g, "/");
      parentPackage = allNodes.find((n) => {
        if (n.type !== "package" || !n.path) return false;
        const normPkgPath = n.path.replace(/\\/g, "/").replace(/\/+$/, "");
        return normalizedPath.startsWith(`${normPkgPath}/`);
      });
    }

    if (parentPackage) {
      crumbs.push({
        id: parentPackage.id,
        label: parentPackage.name,
        kind: parentPackage.type,
      });
    }
  }

  crumbs.push({
    id: drillNode.id,
    label: drillNode.name,
    kind: drillNode.type,
  });

  return crumbs;
}

/**
 * Collapse specific packages, hiding their internal members while keeping
 * the package node itself visible.
 */
export function collapsePackages(
  nodes: GraphNode[],
  edges: GraphEdge[],
  collapsedPackageIds: Set<string>,
): { nodes: GraphNode[]; edges: GraphEdge[] } {
  if (collapsedPackageIds.size === 0) {
    return { nodes, edges };
  }

  const hiddenNodeIds = new Set<string>();
  const packageByHiddenNode = new Map<string, string>();

  for (const pkgId of collapsedPackageIds) {
    const pkgNode = nodes.find((n) => n.id === pkgId);
    if (!pkgNode) continue;

    for (const node of nodes) {
      if (node.id !== pkgId && isDescendant(pkgNode, node, edges)) {
        hiddenNodeIds.add(node.id);
        packageByHiddenNode.set(node.id, pkgId);
      }
    }
  }

  const visibleNodes = nodes.filter((n) => !hiddenNodeIds.has(n.id));

  // Remap or filter edges
  const remappedEdges: GraphEdge[] = [];
  const seenEdgeKeys = new Set<string>();

  for (const edge of edges) {
    const sourceHidden = hiddenNodeIds.has(edge.source);
    const targetHidden = hiddenNodeIds.has(edge.target);

    // Both internal to the same collapsed package: omit
    if (sourceHidden && targetHidden) {
      const srcPkg = packageByHiddenNode.get(edge.source);
      const tgtPkg = packageByHiddenNode.get(edge.target);
      if (srcPkg === tgtPkg) continue;
    }

    const source = sourceHidden ? packageByHiddenNode.get(edge.source)! : edge.source;
    const target = targetHidden ? packageByHiddenNode.get(edge.target)! : edge.target;

    if (source === target) continue;

    const key = `${source}->${target}:${edge.type}`;
    if (!seenEdgeKeys.has(key)) {
      seenEdgeKeys.add(key);
      remappedEdges.push({ source, target, type: edge.type });
    }
  }

  return { nodes: visibleNodes, edges: remappedEdges };
}
