import { memo, useMemo } from "react";
import {
  Background,
  Controls,
  Handle,
  MarkerType,
  MiniMap,
  Position,
  ReactFlow,
  type Edge,
  type Node,
  type NodeProps,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { layoutNodes, visibleEdges } from "./graphLayout";
import { type GraphDocument, type GraphNode, type NodeType, TYPE_LABELS } from "./types";

type ArchitectureNodeData = {
  kind: NodeType;
  title: string;
  subtitle: string | null;
};

type ArchitectureFlowNode = Node<ArchitectureNodeData, "architecture">;

function nodeLocation(node: GraphNode): string | null {
  if (!node.path) return null;
  return node.line_start ? `${node.path}:${node.line_start}` : node.path;
}

const ArchitectureNode = memo(function ArchitectureNode({ data, selected }: NodeProps<ArchitectureFlowNode>) {
  return (
    <div className={`architecture-node ${data.kind} ${selected ? "selected" : ""}`}>
      <Handle type="target" position={Position.Left} className="architecture-handle" />
      <span className="architecture-node-type">{TYPE_LABELS[data.kind]}</span>
      <strong>{data.title}</strong>
      {data.subtitle && <small title={data.subtitle}>{data.subtitle}</small>}
      <Handle type="source" position={Position.Right} className="architecture-handle" />
    </div>
  );
});

const nodeTypes = { architecture: ArchitectureNode };

export function ArchitectureGraph({
  document,
  nodes,
  selectedId,
  onSelect,
  onDrillDown,
}: {
  document: GraphDocument;
  nodes: GraphNode[];
  selectedId: string | null;
  onSelect: (nodeId: string) => void;
  onDrillDown?: (nodeId: string) => void;
}) {
  // 1. Memoize layout positioning so it only computes when nodes list changes (avoids recalculation on selection)
  const positionedNodes = useMemo(() => layoutNodes(nodes), [nodes]);

  // 2. React Flow nodes update selection flag in O(N) without recalculating layout
  const flowNodes = useMemo(() => {
    return positionedNodes.map((node) => ({
      id: node.id,
      type: "architecture" as const,
      position: node.position,
      selected: node.id === selectedId,
      data: { kind: node.type, title: node.name, subtitle: nodeLocation(node) },
    }));
  }, [positionedNodes, selectedId]);

  // 3. Filter visible edges
  const activeEdges = useMemo(
    () => visibleEdges(document.edges, nodes),
    [document.edges, nodes],
  );

  // 4. Highlight connected edges and dim unselected edges for instant clarity
  const flowEdges = useMemo(() => {
    return activeEdges.map((edge, index) => {
      const isConnected = Boolean(selectedId && (edge.source === selectedId || edge.target === selectedId));
      const isDimmed = Boolean(selectedId && !isConnected);

      return {
        id: `${edge.source}-${edge.target}-${edge.type}-${index}`,
        source: edge.source,
        target: edge.target,
        type: "smoothstep",
        label: isConnected || !selectedId ? edge.type : undefined,
        labelStyle: {
          fill: isConnected ? "#e0f2fe" : "#a1a1aa",
          fontSize: 10,
          fontWeight: isConnected ? 600 : 400,
        },
        labelBgStyle: { fill: isConnected ? "#0369a1" : "#0c0c0e", fillOpacity: 0.9 },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: isConnected ? "#38bdf8" : isDimmed ? "#27272a" : "#52525b",
        },
        style: {
          stroke: isConnected ? "#38bdf8" : isDimmed ? "#27272a" : "#52525b",
          strokeWidth: isConnected ? 2 : 1.25,
          opacity: isDimmed ? 0.35 : 1,
        },
        zIndex: isConnected ? 10 : 0,
      } as Edge;
    });
  }, [activeEdges, selectedId]);

  return (
    <ReactFlow
      nodes={flowNodes}
      edges={flowEdges}
      nodeTypes={nodeTypes}
      onNodeClick={(_, node) => onSelect(node.id)}
      onNodeDoubleClick={(_, node) => onDrillDown?.(node.id)}
      fitView
      fitViewOptions={{ padding: 0.22, maxZoom: 1 }}
      minZoom={0.1}
      maxZoom={1.5}
      nodesDraggable={false}
      onlyRenderVisibleElements={true}
      proOptions={{ hideAttribution: true }}
      aria-label="Interactive architecture graph"
    >
      <Background color="#3f3f46" gap={20} size={1} />
      <MiniMap
        ariaLabel="Architecture graph minimap"
        maskColor="rgba(9, 9, 11, 0.68)"
        nodeColor={(node) => {
          const kind = (node.data as ArchitectureNodeData).kind;
          if (kind === "repository" || kind === "package") return "#fbbf24";
          if (kind === "route" || kind === "model") return "#34d399";
          if (kind === "class" || kind === "function" || kind === "method") return "#c084fc";
          return "#60a5fa";
        }}
      />
      <Controls showInteractive={false} />
    </ReactFlow>
  );
}
