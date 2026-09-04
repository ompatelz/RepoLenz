import { useMemo } from "react";
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

function ArchitectureNode({ data, selected }: NodeProps<ArchitectureFlowNode>) {
  return (
    <div className={`architecture-node ${data.kind} ${selected ? "selected" : ""}`}>
      <Handle type="target" position={Position.Left} className="architecture-handle" />
      <span className="architecture-node-type">{TYPE_LABELS[data.kind]}</span>
      <strong>{data.title}</strong>
      {data.subtitle && <small title={data.subtitle}>{data.subtitle}</small>}
      <Handle type="source" position={Position.Right} className="architecture-handle" />
    </div>
  );
}

const nodeTypes = { architecture: ArchitectureNode };

function toFlowNodes(nodes: GraphNode[], selectedId: string | null): ArchitectureFlowNode[] {
  return layoutNodes(nodes)
    .map((node) => {
      return {
        id: node.id,
        type: "architecture",
        position: node.position,
        selected: node.id === selectedId,
        data: { kind: node.type, title: node.name, subtitle: nodeLocation(node) },
      };
    });
}

function toFlowEdges(edges: GraphDocument["edges"]): Edge[] {
  return edges
    .map((edge, index) => ({
      id: `${edge.source}-${edge.target}-${edge.type}-${index}`,
      source: edge.source,
      target: edge.target,
      type: "smoothstep",
      label: edge.type,
      labelStyle: { fill: "#a1a1aa", fontSize: 10 },
      labelBgStyle: { fill: "#0c0c0e", fillOpacity: 0.9 },
      markerEnd: { type: MarkerType.ArrowClosed, color: "#52525b" },
      style: { stroke: "#52525b", strokeWidth: 1.25 },
    }));
}

export function ArchitectureGraph({
  document,
  nodes,
  selectedId,
  onSelect,
}: {
  document: GraphDocument;
  nodes: GraphNode[];
  selectedId: string | null;
  onSelect: (nodeId: string) => void;
}) {
  const flowNodes = useMemo(() => toFlowNodes(nodes, selectedId), [nodes, selectedId]);
  const flowEdges = useMemo(
    () => toFlowEdges(visibleEdges(document.edges, nodes)),
    [document.edges, nodes],
  );

  return (
    <ReactFlow
      nodes={flowNodes}
      edges={flowEdges}
      nodeTypes={nodeTypes}
      onNodeClick={(_, node) => onSelect(node.id)}
      fitView
      fitViewOptions={{ padding: 0.22, maxZoom: 1 }}
      minZoom={0.1}
      maxZoom={1.5}
      nodesDraggable={false}
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
