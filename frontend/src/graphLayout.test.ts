import { describe, expect, it } from "vitest";

import { layoutNodes, visibleEdges } from "./graphLayout";
import { type GraphNode } from "./types";

const nodes: GraphNode[] = [
  { id: "method:run", type: "method", name: "run", path: "service.py", line_start: 8, line_end: 10, metadata: {} },
  { id: "repository:demo", type: "repository", name: "demo", path: ".", line_start: null, line_end: null, metadata: {} },
  { id: "module:service", type: "module", name: "service", path: "service.py", line_start: null, line_end: null, metadata: {} },
  { id: "module:api", type: "module", name: "api", path: "api.py", line_start: null, line_end: null, metadata: {} },
];

describe("graph layout", () => {
  it("places hierarchy types in stable columns", () => {
    const result = layoutNodes(nodes);

    expect(result.map((node) => node.id)).toEqual([
      "repository:demo",
      "module:api",
      "module:service",
      "method:run",
    ]);
    expect(result.find((node) => node.id === "repository:demo")?.position.x).toBe(44);
    expect(result.find((node) => node.id === "module:api")?.position.x).toBe(548);
    expect(result.find((node) => node.id === "module:service")?.position.y).toBe(160);
  });

  it("removes edges whose endpoint is hidden by a filter", () => {
    const result = visibleEdges(
      [
        { source: "repository:demo", target: "module:api", type: "contains" },
        { source: "module:api", target: "method:run", type: "contains" },
      ],
      nodes.filter((node) => node.type !== "method"),
    );

    expect(result).toEqual([{ source: "repository:demo", target: "module:api", type: "contains" }]);
  });
});
