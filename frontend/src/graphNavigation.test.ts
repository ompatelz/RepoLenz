import { describe, expect, it } from "vitest";

import {
  buildBreadcrumbs,
  collapsePackages,
  computeNeighborhood,
  filterDrillDown,
} from "./graphNavigation";
import { type GraphEdge, type GraphNode } from "./types";

const testNodes: GraphNode[] = [
  { id: "repo:root", type: "repository", name: "my-project", path: ".", line_start: null, line_end: null, metadata: {} },
  { id: "pkg:app", type: "package", name: "app", path: "src/app", line_start: null, line_end: null, metadata: {} },
  { id: "mod:app.main", type: "module", name: "app.main", path: "src/app/main.py", line_start: null, line_end: null, metadata: {} },
  { id: "mod:app.service", type: "module", name: "app.service", path: "src/app/service.py", line_start: null, line_end: null, metadata: {} },
  { id: "class:app.service.Service", type: "class", name: "Service", path: "src/app/service.py", line_start: 10, line_end: 25, metadata: {} },
  { id: "fn:app.main.run", type: "function", name: "run", path: "src/app/main.py", line_start: 5, line_end: 15, metadata: {} },
  { id: "pkg:utils", type: "package", name: "utils", path: "src/utils", line_start: null, line_end: null, metadata: {} },
  { id: "mod:utils.helper", type: "module", name: "utils.helper", path: "src/utils/helper.py", line_start: null, line_end: null, metadata: {} },
];

const testEdges: GraphEdge[] = [
  { source: "repo:root", target: "pkg:app", type: "contains" },
  { source: "repo:root", target: "pkg:utils", type: "contains" },
  { source: "pkg:app", target: "mod:app.main", type: "contains" },
  { source: "pkg:app", target: "mod:app.service", type: "contains" },
  { source: "mod:app.main", target: "fn:app.main.run", type: "defines" },
  { source: "mod:app.service", target: "class:app.service.Service", type: "defines" },
  { source: "pkg:utils", target: "mod:utils.helper", type: "contains" },
  { source: "mod:app.main", target: "mod:app.service", type: "imports" },
  { source: "fn:app.main.run", target: "class:app.service.Service", type: "calls" },
  { source: "mod:app.service", target: "mod:utils.helper", type: "imports" },
];

describe("graphNavigation", () => {
  describe("computeNeighborhood", () => {
    it("returns all nodes and edges when depth is 'all'", () => {
      const res = computeNeighborhood(testNodes, testEdges, "mod:app.main", "all");
      expect(res.nodes.length).toBe(testNodes.length);
      expect(res.edges.length).toBe(testEdges.length);
    });

    it("extracts 1-hop neighborhood including incoming and outgoing connections", () => {
      const res = computeNeighborhood(testNodes, testEdges, "mod:app.main", 1);
      const ids = res.nodes.map((n) => n.id);
      expect(ids).toContain("mod:app.main");
      // Connected via contains from pkg:app
      expect(ids).toContain("pkg:app");
      // Connected via defines to fn:app.main.run
      expect(ids).toContain("fn:app.main.run");
      // Connected via imports to mod:app.service
      expect(ids).toContain("mod:app.service");
      // 2-hop away nodes should not be present
      expect(ids).not.toContain("mod:utils.helper");
      expect(ids).not.toContain("repo:root");
    });

    it("extracts 2-hop neighborhood", () => {
      const res = computeNeighborhood(testNodes, testEdges, "mod:app.main", 2);
      const ids = res.nodes.map((n) => n.id);
      expect(ids).toContain("mod:app.main");
      expect(ids).toContain("repo:root"); // 2 hops: mod:app.main <- pkg:app <- repo:root
      expect(ids).toContain("class:app.service.Service"); // 2 hops: mod:app.main -> mod:app.service -> class
      expect(ids).toContain("mod:utils.helper"); // 2 hops: mod:app.main -> mod:app.service -> mod:utils.helper
    });
  });

  describe("filterDrillDown", () => {
    it("returns all nodes when drillNode is null", () => {
      const res = filterDrillDown(testNodes, testEdges, null);
      expect(res.length).toBe(testNodes.length);
    });

    it("filters to package and its descendant modules and symbols", () => {
      const pkgNode = testNodes.find((n) => n.id === "pkg:app")!;
      const res = filterDrillDown(testNodes, testEdges, pkgNode);
      const ids = res.map((n) => n.id);

      expect(ids).toContain("pkg:app");
      expect(ids).toContain("mod:app.main");
      expect(ids).toContain("mod:app.service");
      expect(ids).toContain("fn:app.main.run");
      expect(ids).toContain("class:app.service.Service");
      // Unrelated package nodes must not be present
      expect(ids).not.toContain("pkg:utils");
      expect(ids).not.toContain("mod:utils.helper");
      expect(ids).not.toContain("repo:root");
    });

    it("filters to module and its contained symbols", () => {
      const modNode = testNodes.find((n) => n.id === "mod:app.main")!;
      const res = filterDrillDown(testNodes, testEdges, modNode);
      const ids = res.map((n) => n.id);

      expect(ids).toContain("mod:app.main");
      expect(ids).toContain("fn:app.main.run");
      expect(ids).not.toContain("class:app.service.Service");
      expect(ids).not.toContain("mod:app.service");
    });
  });

  describe("buildBreadcrumbs", () => {
    it("returns Root breadcrumb when not drilled down", () => {
      const crumbs = buildBreadcrumbs(null, testNodes, testEdges);
      expect(crumbs).toEqual([{ id: null, label: "All" }]);
    });

    it("returns Package breadcrumb when drilled into a package", () => {
      const pkgNode = testNodes.find((n) => n.id === "pkg:app")!;
      const crumbs = buildBreadcrumbs(pkgNode, testNodes, testEdges);
      expect(crumbs).toEqual([
        { id: null, label: "All" },
        { id: "pkg:app", label: "app", kind: "package" },
      ]);
    });

    it("returns Package > Module breadcrumbs when drilled into a module", () => {
      const modNode = testNodes.find((n) => n.id === "mod:app.main")!;
      const crumbs = buildBreadcrumbs(modNode, testNodes, testEdges);
      expect(crumbs).toEqual([
        { id: null, label: "All" },
        { id: "pkg:app", label: "app", kind: "package" },
        { id: "mod:app.main", label: "app.main", kind: "module" },
      ]);
    });
  });

  describe("collapsePackages", () => {
    it("hides internal package members when package is collapsed", () => {
      const collapsed = new Set(["pkg:app"]);
      const res = collapsePackages(testNodes, testEdges, collapsed);
      const ids = res.nodes.map((n) => n.id);

      expect(ids).toContain("pkg:app");
      expect(ids).not.toContain("mod:app.main");
      expect(ids).not.toContain("mod:app.service");
      expect(ids).not.toContain("fn:app.main.run");
      expect(ids).not.toContain("class:app.service.Service");
      // Other package should remain expanded
      expect(ids).toContain("pkg:utils");
      expect(ids).toContain("mod:utils.helper");

      // Check remapped edge: mod:app.service -> mod:utils.helper becomes pkg:app -> mod:utils.helper
      const remapped = res.edges.find((e) => e.source === "pkg:app" && e.target === "mod:utils.helper");
      expect(remapped).toBeDefined();
    });
  });
});
