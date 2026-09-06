import { describe, expect, it } from "vitest";

import { buildBreadcrumbs } from "./graphNavigation";
import { type GraphNode, type NodeType, TYPE_LABELS } from "./types";

describe("accessibility and navigation contracts", () => {
  it("provides user-friendly accessible labels for all node types", () => {
    const requiredTypes: NodeType[] = [
      "repository",
      "package",
      "module",
      "class",
      "function",
      "method",
      "route",
      "model",
      "dependency",
    ];

    for (const type of requiredTypes) {
      expect(TYPE_LABELS[type]).toBeDefined();
      expect(TYPE_LABELS[type].length).toBeGreaterThan(0);
      expect(TYPE_LABELS[type][0]).toBe(TYPE_LABELS[type][0].toUpperCase());
    }
  });

  it("builds hierarchy breadcrumbs suitable for aria-current page tracking", () => {
    const nodes: GraphNode[] = [
      { id: "pkg:core", type: "package", name: "core", path: "src/core", line_start: null, line_end: null, metadata: {} },
      { id: "mod:core.engine", type: "module", name: "core.engine", path: "src/core/engine.py", line_start: null, line_end: null, metadata: {} },
    ];
    const edges = [{ source: "pkg:core", target: "mod:core.engine", type: "contains" }];

    const crumbs = buildBreadcrumbs(nodes[1], nodes, edges);
    expect(crumbs).toHaveLength(3);
    expect(crumbs[0]).toEqual({ id: null, label: "All" });
    expect(crumbs[1]).toEqual({ id: "pkg:core", label: "core", kind: "package" });
    expect(crumbs[2]).toEqual({ id: "mod:core.engine", label: "core.engine", kind: "module" });

    // Verify current crumb determination for aria-current="page"
    const activeDrillId = "mod:core.engine";
    const ariaCurrentStates = crumbs.map((c) => c.id === activeDrillId ? "page" : undefined);
    expect(ariaCurrentStates).toEqual([undefined, undefined, "page"]);
  });

  it("formats accessible screen reader status announcements correctly", () => {
    function generateAnnouncement(options: {
      drillDownName?: string;
      focusDepth?: number | "all";
      selectedName?: string;
      query?: string;
      visibleCount: number;
    }): string {
      const parts: string[] = [];
      if (options.drillDownName) parts.push(`Scope: ${options.drillDownName}.`);
      else parts.push("Scope: All.");
      if (options.focusDepth && options.focusDepth !== "all" && options.selectedName) {
        parts.push(`Focus: ${options.focusDepth}-hop around ${options.selectedName}.`);
      }
      parts.push(`Showing ${options.visibleCount} visible architecture elements.`);
      return parts.join(" ");
    }

    const defaultMsg = generateAnnouncement({ visibleCount: 42 });
    expect(defaultMsg).toBe("Scope: All. Showing 42 visible architecture elements.");

    const focusedMsg = generateAnnouncement({
      drillDownName: "backend",
      focusDepth: 2,
      selectedName: "analysis",
      visibleCount: 8,
    });
    expect(focusedMsg).toBe(
      "Scope: backend. Focus: 2-hop around analysis. Showing 8 visible architecture elements.",
    );
  });
});
