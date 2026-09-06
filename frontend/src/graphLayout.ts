import { type GraphDocument, type GraphNode, type NodeType } from "./types";

export type PositionedGraphNode = GraphNode & { position: { x: number; y: number } };

const TYPE_RANK: Record<NodeType, number> = {
  repository: 0,
  package: 1,
  module: 2,
  route: 3,
  model: 3,
  class: 3,
  component: 3,
  function: 4,
  method: 4,
  dependency: 5,
};

/**
 * Place the static hierarchy in deterministic columns before React Flow renders it.
 * This avoids a force-layout dependency and keeps successive refreshes stable.
 */
export function layoutNodes(nodes: GraphNode[]): PositionedGraphNode[] {
  const rowsByRank = new Map<number, number>();
  return [...nodes]
    .sort((left, right) => {
      const rank = TYPE_RANK[left.type] - TYPE_RANK[right.type];
      return rank || left.name.localeCompare(right.name) || left.id.localeCompare(right.id);
    })
    .map((node) => {
      const rank = TYPE_RANK[node.type];
      const row = rowsByRank.get(rank) ?? 0;
      rowsByRank.set(rank, row + 1);
      return { ...node, position: { x: 44 + rank * 252, y: 44 + row * 116 } };
    });
}

/** Keep only relationships that remain meaningful after a graph filter is applied. */
export function visibleEdges(
  edges: GraphDocument["edges"],
  nodes: GraphNode[],
): GraphDocument["edges"] {
  const nodeIds = new Set(nodes.map((node) => node.id));
  return edges.filter((edge) => nodeIds.has(edge.source) && nodeIds.has(edge.target));
}
