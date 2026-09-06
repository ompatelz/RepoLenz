export type NodeType =
  | "repository"
  | "package"
  | "module"
  | "class"
  | "function"
  | "method"
  | "route"
  | "model"
  | "component"
  | "dependency";

export type GraphNode = {
  id: string;
  type: NodeType;
  name: string;
  path: string | null;
  line_start: number | null;
  line_end: number | null;
  metadata: Record<string, unknown>;
};

export type GraphEdge = { source: string; target: string; type: string };

export type GraphDocument = {
  metadata: Record<string, unknown>;
  nodes: GraphNode[];
  edges: GraphEdge[];
};

export const TYPE_LABELS: Record<NodeType, string> = {
  repository: "Repository",
  package: "Package",
  module: "Module",
  class: "Class",
  function: "Function",
  method: "Method",
  route: "Route",
  model: "Model",
  component: "Component",
  dependency: "Dependency",
};

export type GraphLevel = "all" | "repository" | "module" | "symbol";

export type FocusDepth = "all" | 1 | 2 | 3;

export type BreadcrumbItem = {
  id: string | null;
  label: string;
  kind?: NodeType;
};
