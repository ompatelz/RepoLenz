import { useCallback, useDeferredValue, useEffect, useMemo, useRef, useState } from "react";

import { ArchitectureGraph } from "./ArchitectureGraph";
import {
  buildBreadcrumbs,
  collapsePackages,
  computeNeighborhood,
  filterDrillDown,
} from "./graphNavigation";
import {
  type FocusDepth,
  type GraphDocument,
  type GraphLevel,
  type GraphNode,
  type NodeExplanation,
  type NodeType,
  TYPE_LABELS,
} from "./types";


type ApiStats = {
  nodes: number;
  edges: number;
  cycles: number;
  routes?: number;
  models?: number;
};
type LoadState = "loading" | "ready" | "error";

async function getJson<T>(url: string): Promise<T> {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Request failed (${response.status})`);
  return response.json() as Promise<T>;
}

function nodeLocation(node: GraphNode): string | null {
  return node.path ? (node.line_start ? `${node.path}:${node.line_start}` : node.path) : null;
}

export function parseRouteDetails(node: GraphNode): { method: string; path: string } {
  let method = typeof node.metadata.method === "string" ? node.metadata.method : "";
  let path = typeof node.metadata.path === "string" ? node.metadata.path : "";
  if (!method || !path) {
    const parts = node.name.split(" ");
    if (parts.length >= 2) {
      method = method || parts[0];
      path = path || parts.slice(1).join(" ");
    } else {
      method = method || "GET";
      path = path || node.name;
    }
  }
  return {
    method: method.toUpperCase(),
    path,
  };
}

export type ExplorerView = "architecture" | "graph" | "modules" | "routes" | "models";

export function App() {
  const [activeView, setActiveView] = useState<ExplorerView>("architecture");
  const [state, setState] = useState<LoadState>("loading");
  const [graph, setGraph] = useState<GraphDocument | null>(null);
  const [stats, setStats] = useState<ApiStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [level, setLevel] = useState<GraphLevel>("all");
  const [query, setQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState<NodeType | "all">("all");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [drillDownNodeId, setDrillDownNodeId] = useState<string | null>(null);
  const [focusDepth, setFocusDepth] = useState<FocusDepth>("all");
  const [collapsedPackageIds, setCollapsedPackageIds] = useState<Set<string>>(new Set());
  const [explanation, setExplanation] = useState<NodeExplanation | null>(null);
  const [explanationLoading, setExplanationLoading] = useState(false);
  const [explanationError, setExplanationError] = useState<string | null>(null);

  const searchInputRef = useRef<HTMLInputElement>(null);
  const [copiedId, setCopiedId] = useState(false);

  const handleCopyId = useCallback((text: string) => {
    if (navigator.clipboard) {
      void navigator.clipboard.writeText(text);
      setCopiedId(true);
      setTimeout(() => setCopiedId(false), 1500);
    }
  }, []);

  // Clear explanation when selection changes
  useEffect(() => {
    setExplanation(null);
    setExplanationError(null);
    setExplanationLoading(false);
  }, [selectedId]);

  const requestExplanation = useCallback(async (nodeId: string) => {
    setExplanationLoading(true);
    setExplanationError(null);
    try {
      const response = await fetch(`/api/nodes/${encodeURIComponent(nodeId)}/explain`, {
        method: "POST",
      });
      if (!response.ok) {
        throw new Error(`Explanation failed (${response.status})`);
      }
      const data = (await response.json()) as NodeExplanation;
      setExplanation(data);
    } catch (err) {
      setExplanationError(err instanceof Error ? err.message : "Failed to load explanation.");
    } finally {
      setExplanationLoading(false);
    }
  }, []);


  // Keyboard navigation & shortcuts
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Focus search on '/' or 'Ctrl+K' / 'Cmd+K' when not already typing in an input
      if (
        (event.key === "/" || ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k")) &&
        document.activeElement?.tagName !== "INPUT" &&
        document.activeElement?.tagName !== "SELECT" &&
        document.activeElement?.tagName !== "TEXTAREA"
      ) {
        event.preventDefault();
        searchInputRef.current?.focus();
      } else if (event.key === "Escape") {
        if (selectedId) {
          setSelectedId(null);
          setFocusDepth("all");
        } else if (drillDownNodeId) {
          setDrillDownNodeId(null);
        } else if (query) {
          setQuery("");
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [drillDownNodeId, query, selectedId]);

  const load = useCallback(async (targetLevel: GraphLevel = level) => {
    setState("loading");
    setError(null);
    try {
      const url = targetLevel === "all" ? "/api/graph" : `/api/graph?level=${targetLevel}`;
      const [nextGraph, nextStats] = await Promise.all([
        getJson<GraphDocument>(url),
        getJson<ApiStats>("/api/stats"),
      ]);
      setGraph(nextGraph);
      setStats(nextStats);
      setSelectedId((current) =>
        current && nextGraph.nodes.some((node) => node.id === current) ? current : null,
      );
      setDrillDownNodeId((current) =>
        current && nextGraph.nodes.some((node) => node.id === current) ? current : null,
      );
      setState("ready");
    } catch (caught) {
      setGraph(null);
      setStats(null);
      setState("error");
      setError(caught instanceof Error ? caught.message : "Could not contact the RepoLens API.");
    }
  }, [level]);

  useEffect(() => {
    void load(level);
  }, [level, load]);

  const handleLevelChange = (nextLevel: GraphLevel) => {
    if (nextLevel === level) return;
    setLevel(nextLevel);
  };

  const deferredQuery = useDeferredValue(query);

  const nodeMap = useMemo(() => {
    const map = new Map<string, GraphNode>();
    if (graph) {
      for (const node of graph.nodes) {
        map.set(node.id, node);
      }
    }
    return map;
  }, [graph]);

  const typeCounts = useMemo(() => {
    const counts = { module: 0, route: 0, model: 0 };
    if (graph) {
      for (const node of graph.nodes) {
        if (node.type === "module") counts.module++;
        else if (node.type === "route") counts.route++;
        else if (node.type === "model") counts.model++;
      }
    }
    return counts;
  }, [graph]);

  const routeNodes = useMemo(() => {
    if (!graph) return [];
    return graph.nodes.filter((node) => node.type === "route");
  }, [graph]);

  const modelNodes = useMemo(() => {
    if (!graph) return [];
    return graph.nodes.filter((node) => node.type === "model");
  }, [graph]);

  const moduleNodes = useMemo(() => {
    if (!graph) return [];
    return graph.nodes.filter((node) => node.type === "module");
  }, [graph]);

  const filteredRoutes = useMemo(() => {
    const q = deferredQuery.trim().toLowerCase();
    if (!q) return routeNodes;
    return routeNodes.filter(
      (r) =>
        r.name.toLowerCase().includes(q) ||
        (r.path && r.path.toLowerCase().includes(q)) ||
        (typeof r.metadata.handler === "string" && r.metadata.handler.toLowerCase().includes(q)),
    );
  }, [deferredQuery, routeNodes]);

  const filteredModels = useMemo(() => {
    const q = deferredQuery.trim().toLowerCase();
    if (!q) return modelNodes;
    return modelNodes.filter(
      (m) =>
        m.name.toLowerCase().includes(q) ||
        (m.path && m.path.toLowerCase().includes(q)) ||
        (typeof m.metadata.table_name === "string" &&
          m.metadata.table_name.toLowerCase().includes(q)),
    );
  }, [deferredQuery, modelNodes]);

  const filteredModules = useMemo(() => {
    const q = deferredQuery.trim().toLowerCase();
    if (!q) return moduleNodes;
    return moduleNodes.filter(
      (m) => m.name.toLowerCase().includes(q) || (m.path && m.path.toLowerCase().includes(q)),
    );
  }, [deferredQuery, moduleNodes]);

  const drillDownNode = useMemo(
    () => (drillDownNodeId ? nodeMap.get(drillDownNodeId) ?? null : null),
    [drillDownNodeId, nodeMap],
  );

  const breadcrumbs = useMemo(
    () => buildBreadcrumbs(drillDownNode, graph?.nodes ?? [], graph?.edges ?? []),
    [drillDownNode, graph],
  );

  // Progressive graph filtering pipeline:
  // 1. Collapsed packages
  // 2. Drill-down scope
  // 3. Neighborhood focus mode
  // 4. Search query and type filter
  const processedGraph = useMemo(() => {
    if (!graph) return { nodes: [], edges: [] };

    // 1. Collapsed packages
    let nodes = graph.nodes;
    let edges = graph.edges;
    if (collapsedPackageIds.size > 0) {
      const collapsed = collapsePackages(nodes, edges, collapsedPackageIds);
      nodes = collapsed.nodes;
      edges = collapsed.edges;
    }

    // 2. Drill-down scope
    if (drillDownNode) {
      nodes = filterDrillDown(nodes, edges, drillDownNode);
    }

    // 3. Focus mode around selected node
    if (focusDepth !== "all" && selectedId) {
      const focused = computeNeighborhood(nodes, edges, selectedId, focusDepth);
      nodes = focused.nodes;
      edges = focused.edges;
    }

    return { nodes, edges };
  }, [collapsedPackageIds, drillDownNode, focusDepth, graph, selectedId]);

  const nodeTypes = useMemo(
    () => new Set(processedGraph.nodes.map((node) => node.type)),
    [processedGraph.nodes],
  );

  const visibleNodes = useMemo(() => {
    const normalized = deferredQuery.trim().toLocaleLowerCase();
    return processedGraph.nodes.filter((node) => {
      const matchesType = typeFilter === "all" || node.type === typeFilter;
      const matchesQuery =
        !normalized ||
        [node.name, node.path, node.type]
          .filter(Boolean)
          .some((value) => value?.toLocaleLowerCase().includes(normalized));
      return matchesType && matchesQuery;
    });
  }, [deferredQuery, processedGraph.nodes, typeFilter]);

  const selected = useMemo(
    () => (selectedId ? nodeMap.get(selectedId) ?? null : null),
    [nodeMap, selectedId],
  );

  const selectedEdges = useMemo(
    () => (graph?.edges ?? []).filter((edge) => edge.source === selectedId || edge.target === selectedId),
    [graph, selectedId],
  );

  const inspectNodeOnGraph = useCallback((nodeId: string) => {
    setDrillDownNodeId(null);
    setTypeFilter("all");
    setSelectedId(nodeId);
    setActiveView("architecture");
  }, []);

  const cards = [
    { label: "Nodes", value: stats?.nodes ?? "—", detail: "Architecture elements" },
    { label: "Relationships", value: stats?.edges ?? "—", detail: "Static evidence links" },
    { label: "Cycles", value: stats?.cycles ?? "—", detail: "Dependency cycles" },
    {
      label: "Visible",
      value:
        state === "ready"
          ? activeView === "routes"
            ? filteredRoutes.length
            : activeView === "models"
              ? filteredModels.length
              : activeView === "modules"
                ? filteredModules.length
                : visibleNodes.length
          : "—",
      detail:
        activeView === "routes"
          ? "Matched routes"
          : activeView === "models"
            ? "Matched models"
            : activeView === "modules"
              ? "Matched modules"
              : "Current map filter",
    },
  ];
  const repositoryName =
    typeof graph?.metadata.repository === "string" ? graph.metadata.repository : "Local repository";

  const handleNodeDoubleClick = (nodeId: string) => {
    const targetNode = nodeMap.get(nodeId);
    if (targetNode && (targetNode.type === "package" || targetNode.type === "module")) {
      setDrillDownNodeId(targetNode.id);
    }
  };

  return (
    <main className="app-shell">
      <header className="topbar">
        <a className="brand" href="/" aria-label="RepoLens home">
          <span className="brand-mark" aria-hidden="true">⌘</span>
          <span>RepoLens</span>
          <span className="beta">LOCAL</span>
        </a>
        <div className="repository-picker" aria-label="Active repository">
          <span className={`status-dot ${state === "ready" ? "" : "muted"}`} />
          <span className="repo-name">
            {state === "ready" ? repositoryName : "No repository loaded"}
          </span>
        </div>
        <div className="topbar-actions">
          <button className="button secondary" onClick={() => void load(level)} type="button">
            Refresh
          </button>
        </div>
      </header>
      <section className="workspace">
        <aside className="sidebar" aria-label="Project navigation">
          <div className="sidebar-heading">EXPLORER</div>
          <nav className="sidebar-nav">
            <button
              type="button"
              className={`nav-item ${activeView === "architecture" ? "active" : ""}`}
              onClick={() => {
                setActiveView("architecture");
                setTypeFilter("all");
                setDrillDownNodeId(null);
                setQuery("");
              }}
              aria-label="View architecture map"
            >
              <span>◇</span> Architecture
            </button>
            <button
              type="button"
              className={`nav-item ${activeView === "graph" ? "active" : ""}`}
              onClick={() => {
                setActiveView("graph");
                setTypeFilter("all");
              }}
              aria-label="View full dependency graph"
            >
              <span>□</span> Graph <b>{stats?.nodes ?? 0}</b>
            </button>
            <button
              type="button"
              className={`nav-item ${activeView === "modules" ? "active" : ""}`}
              onClick={() => {
                setActiveView("modules");
              }}
              aria-label="View modules directory"
            >
              <span>⌘</span> Modules <b>{typeCounts.module}</b>
            </button>
            <button
              type="button"
              className={`nav-item ${activeView === "routes" ? "active" : ""}`}
              onClick={() => {
                setActiveView("routes");
              }}
              aria-label="View API routes catalog"
            >
              <span>⚡</span> Routes <b>{typeCounts.route}</b>
            </button>
            <button
              type="button"
              className={`nav-item ${activeView === "models" ? "active" : ""}`}
              onClick={() => {
                setActiveView("models");
              }}
              aria-label="View database models catalog"
            >
              <span>⛁</span> Models <b>{typeCounts.model}</b>
            </button>
          </nav>
          <div className="sidebar-footer">
            <div className="sidebar-heading">ANALYSIS</div>
            <div className="muted-line"><span className={`status-dot ${state === "ready" ? "" : "muted"}`} /> {state === "ready" ? "Static analysis ready" : "Waiting for local API"}</div>
            <p>RepoLens reads code statically. Your repository is never executed.</p>
          </div>
        </aside>
        <section className="content" id="architecture">
          <div className="content-header">
            <div>
              <p className="eyebrow">
                {activeView === "architecture" && "ARCHITECTURE MAP"}
                {activeView === "graph" && "DEPENDENCY GRAPH"}
                {activeView === "modules" && "MODULES DIRECTORY"}
                {activeView === "routes" && "API ROUTES CATALOG"}
                {activeView === "models" && "DATABASE MODELS CATALOG"}
              </p>
              <h1>
                {activeView === "architecture" && "Understand the shape of your codebase."}
                {activeView === "graph" && "Interactive node relationship graph."}
                {activeView === "modules" && "All detected modules and packages."}
                {activeView === "routes" && "All public HTTP endpoints and handlers."}
                {activeView === "models" && "All database ORM models and tables."}
              </h1>
            </div>
            <div className="header-actions">
              {activeView !== "architecture" && activeView !== "graph" && (
                <button
                  className="button secondary"
                  onClick={() => setActiveView("architecture")}
                  type="button"
                >
                  Back to Architecture Map
                </button>
              )}
              {selected && (
                <button className="button secondary" onClick={() => { setSelectedId(null); setFocusDepth("all"); }} type="button">
                  Clear selection
                </button>
              )}
            </div>
          </div>
          <div className="stats-grid">
            {cards.map((stat) => <article className="stat-card" key={stat.label}><p>{stat.label}</p><strong>{stat.value}</strong><span>{stat.detail}</span></article>)}
          </div>
          {(activeView === "architecture" || activeView === "graph") && (
            <section className="graph-panel" id="map" aria-label="Architecture graph">
              {state === "loading" && <div className="state-card"><span className="spinner" /><h2>Loading architecture map</h2><p>Reading the local analysis API…</p></div>}
              {state === "error" && <div className="state-card"><div className="empty-icon">!</div><h2>Could not load the map</h2><p>{error ?? "Start RepoLens with repolens serve <path>, then refresh."}</p><button className="button primary" onClick={() => void load(level)} type="button">Try again</button></div>}
              {state === "ready" && graph && graph.nodes.length === 0 && <div className="state-card"><div className="empty-icon">◇</div><h2>No architecture nodes found</h2><p>This level or analysis produced no graph nodes. Try switching to "All" or a repository with Python source files.</p><button className="button secondary" onClick={() => handleLevelChange("all")} type="button">Switch to All</button></div>}
              {state === "ready" && graph && graph.nodes.length > 0 && <div className="graph-workspace">
                {/* Breadcrumb Navigation Bar */}
                <nav className="breadcrumbs-bar" aria-label="Hierarchy breadcrumbs">
                  <span className="breadcrumbs-label">Scope:</span>
                  {breadcrumbs.map((crumb, index) => {
                    const isCurrent = crumb.id === drillDownNodeId;
                    return (
                      <span key={crumb.id ?? "root"} className="breadcrumb-segment">
                        {index > 0 && <span className="breadcrumb-sep" aria-hidden="true">/</span>}
                        <button
                          type="button"
                          className={`breadcrumb-btn ${isCurrent ? "current" : ""}`}
                          onClick={() => setDrillDownNodeId(crumb.id)}
                          aria-current={isCurrent ? "page" : undefined}
                          title={`Navigate to ${crumb.label}`}
                        >
                          {crumb.kind && <span className={`crumb-kind ${crumb.kind}`}>{crumb.kind}</span>}
                          {crumb.label}
                        </button>
                      </span>
                    );
                  })}
                  {drillDownNode && (
                    <button
                      type="button"
                      className="breadcrumb-reset-btn"
                      onClick={() => setDrillDownNodeId(null)}
                      title="Exit drill-down scope"
                    >
                      Reset scope
                    </button>
                  )}
                  {focusDepth !== "all" && selected && (
                    <span className="focus-badge" title={`Focused on ${selected.name} (${focusDepth} hop${Number(focusDepth) > 1 ? "s" : ""})`}>
                      Focus: {focusDepth}-hop ({selected.name})
                      <button type="button" onClick={() => setFocusDepth("all")} aria-label="Clear focus">×</button>
                    </span>
                  )}
                </nav>

                {/* Screen reader live announcements */}
                <div className="sr-only" aria-live="polite" aria-atomic="true">
                  {drillDownNode ? `Scope: ${drillDownNode.name}. ` : "Scope: All. "}
                  {focusDepth !== "all" && selected ? `Focus: ${focusDepth}-hop around ${selected.name}. ` : ""}
                  {`Showing ${visibleNodes.length} visible architecture elements.`}
                </div>

                <div className="map-toolbar">
                  {/* Level Selector Tabs */}
                  <div className="level-tabs" role="tablist" aria-label="Architecture hierarchy levels">
                    {(["all", "repository", "module", "symbol"] as const).map((lvl) => {
                      const labels: Record<typeof lvl, string> = {
                        all: "All",
                        repository: "Repo",
                        module: "Modules",
                        symbol: "Symbols",
                      };
                      return (
                        <button
                          key={lvl}
                          id={`level-tab-${lvl}`}
                          type="button"
                          role="tab"
                          aria-selected={level === lvl}
                          aria-controls="map"
                          className={`level-tab ${level === lvl ? "active" : ""}`}
                          onClick={() => handleLevelChange(lvl)}
                        >
                          {labels[lvl]}
                        </button>
                      );
                    })}
                  </div>

                  <label className="search-label" htmlFor="node-search-input">
                    <span className="sr-only">Search nodes</span>
                    <input
                      id="node-search-input"
                      ref={searchInputRef}
                      value={query}
                      onChange={(event) => setQuery(event.target.value)}
                      placeholder="Search names, paths, or types… (Press '/' to focus)"
                      aria-label="Search architecture nodes"
                    />
                  </label>

                  <select value={typeFilter} onChange={(event) => setTypeFilter(event.target.value as NodeType | "all")} aria-label="Filter by node type">
                    <option value="all">All node types</option>
                    {Object.entries(TYPE_LABELS).filter(([type]) => nodeTypes.has(type as NodeType)).map(([type, label]) => <option key={type} value={type}>{label}</option>)}
                  </select>

                  <select
                    value={focusDepth}
                    onChange={(e) => setFocusDepth(e.target.value === "all" ? "all" : (Number(e.target.value) as 1 | 2 | 3))}
                    aria-label="Neighborhood focus depth"
                    disabled={!selectedId}
                    title={!selectedId ? "Select a node to focus on its neighborhood" : "Filter to neighborhood"}
                    className="focus-select"
                  >
                    <option value="all">Focus: Off</option>
                    <option value="1">Focus: 1-hop</option>
                    <option value="2">Focus: 2-hop</option>
                    <option value="3">Focus: 3-hop</option>
                  </select>
                </div>

                {visibleNodes.length === 0 ? (
                  <div className="no-results">
                    <strong>No matching nodes</strong>
                    <span>Adjust search, reset filters, or exit focus/drill-down mode.</span>
                    <div className="no-results-actions">
                      {query && <button className="button secondary" onClick={() => setQuery("")} type="button">Clear search</button>}
                      {typeFilter !== "all" && <button className="button secondary" onClick={() => setTypeFilter("all")} type="button">All types</button>}
                      {drillDownNode && <button className="button secondary" onClick={() => setDrillDownNodeId(null)} type="button">Reset scope</button>}
                      {focusDepth !== "all" && <button className="button secondary" onClick={() => setFocusDepth("all")} type="button">Reset focus</button>}
                    </div>
                  </div>
                ) : (
                  <ArchitectureGraph
                    document={graph}
                    nodes={visibleNodes}
                    selectedId={selectedId}
                    onSelect={setSelectedId}
                    onDrillDown={handleNodeDoubleClick}
                  />
                )}
              </div>}
              <div className="graph-legend"><span><i className="dot module" /> Module</span><span><i className="dot symbol" /> Symbol</span><span><i className="dot route" /> Route</span><span><i className="dot model" /> Model</span></div>
            </section>
          )}

          {activeView === "routes" && (
            <section className="catalog-panel" aria-label="API Routes Catalog">
              <div className="catalog-header">
                <div>
                  <h2>API Routes ({routeNodes.length})</h2>
                  <p className="muted-copy">Detected HTTP endpoints mapped across application routers and handlers.</p>
                </div>
                <div className="catalog-search">
                  <input
                    ref={searchInputRef}
                    type="search"
                    className="catalog-input"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Search routes or handlers… (Press '/' to focus)"
                    aria-label="Filter routes"
                  />
                  {query && (
                    <button className="button secondary" onClick={() => setQuery("")} type="button">
                      Clear
                    </button>
                  )}
                </div>
              </div>

              {state === "loading" && <div className="state-card"><span className="spinner" /><h2>Loading routes…</h2></div>}
              {state === "error" && <div className="state-card"><div className="empty-icon">!</div><h2>Could not load routes</h2><p>{error}</p></div>}
              {state === "ready" && filteredRoutes.length === 0 && (
                <div className="no-results">
                  <strong>No routes match your search</strong>
                  <span>Try a different query or clear the filter.</span>
                  {query && (
                    <button className="button secondary" style={{ marginTop: 8 }} onClick={() => setQuery("")} type="button">
                      Clear search
                    </button>
                  )}
                </div>
              )}
              {state === "ready" && filteredRoutes.length > 0 && (
                <div className="catalog-table-wrap">
                  <table className="catalog-table">
                    <thead>
                      <tr>
                        <th style={{ width: 90 }}>Method</th>
                        <th>Path</th>
                        <th>Handler</th>
                        <th>Location</th>
                        <th style={{ width: 150, textAlign: "right" }}>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredRoutes.map((route) => {
                        const { method, path } = parseRouteDetails(route);
                        const methodClass = method.toLowerCase();
                        const loc = nodeLocation(route);
                        return (
                          <tr key={route.id}>
                            <td>
                              <span className={`method-pill ${methodClass}`}>{method}</span>
                            </td>
                            <td>
                              <code className="route-path-text">{path}</code>
                            </td>
                            <td>
                              <code>{typeof route.metadata.handler === "string" ? route.metadata.handler : "—"}</code>
                            </td>
                            <td>
                              <span className="muted-copy">{loc ?? "—"}</span>
                            </td>
                            <td style={{ textAlign: "right" }}>
                              <button
                                type="button"
                                className="inspect-btn"
                                onClick={() => inspectNodeOnGraph(route.id)}
                                title={`Inspect ${route.name} on graph`}
                              >
                                Inspect on Graph ↗
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
          )}

          {activeView === "models" && (
            <section className="catalog-panel" aria-label="Database Models Catalog">
              <div className="catalog-header">
                <div>
                  <h2>Database Models ({modelNodes.length})</h2>
                  <p className="muted-copy">Detected ORM schemas, database entities, and persistent data models.</p>
                </div>
                <div className="catalog-search">
                  <input
                    ref={searchInputRef}
                    type="search"
                    className="catalog-input"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Search models or table names… (Press '/' to focus)"
                    aria-label="Filter models"
                  />
                  {query && (
                    <button className="button secondary" onClick={() => setQuery("")} type="button">
                      Clear
                    </button>
                  )}
                </div>
              </div>

              {state === "loading" && <div className="state-card"><span className="spinner" /><h2>Loading models…</h2></div>}
              {state === "error" && <div className="state-card"><div className="empty-icon">!</div><h2>Could not load models</h2><p>{error}</p></div>}
              {state === "ready" && filteredModels.length === 0 && (
                <div className="no-results">
                  <strong>No models match your search</strong>
                  <span>Try a different query or clear the filter.</span>
                  {query && (
                    <button className="button secondary" style={{ marginTop: 8 }} onClick={() => setQuery("")} type="button">
                      Clear search
                    </button>
                  )}
                </div>
              )}
              {state === "ready" && filteredModels.length > 0 && (
                <div className="catalog-table-wrap">
                  <table className="catalog-table">
                    <thead>
                      <tr>
                        <th>Model Name</th>
                        <th>Table Name</th>
                        <th>Inherits / Bases</th>
                        <th>Location</th>
                        <th style={{ width: 150, textAlign: "right" }}>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredModels.map((model) => {
                        const tableName = typeof model.metadata.table_name === "string" ? model.metadata.table_name : null;
                        const bases = Array.isArray(model.metadata.bases)
                          ? model.metadata.bases.join(", ")
                          : typeof model.metadata.bases === "string"
                          ? model.metadata.bases
                          : null;
                        const loc = nodeLocation(model);
                        return (
                          <tr key={model.id}>
                            <td>
                              <strong>{model.name}</strong>
                            </td>
                            <td>
                              <code>{tableName ?? "—"}</code>
                            </td>
                            <td>
                              <code>{bases ?? "—"}</code>
                            </td>
                            <td>
                              <span className="muted-copy">{loc ?? "—"}</span>
                            </td>
                            <td style={{ textAlign: "right" }}>
                              <button
                                type="button"
                                className="inspect-btn"
                                onClick={() => inspectNodeOnGraph(model.id)}
                                title={`Inspect ${model.name} on graph`}
                              >
                                Inspect on Graph ↗
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
          )}

          {activeView === "modules" && (
            <section className="catalog-panel" aria-label="Modules Directory">
              <div className="catalog-header">
                <div>
                  <h2>Modules Directory ({moduleNodes.length})</h2>
                  <p className="muted-copy">Detected Python modules and packages across the repository hierarchy.</p>
                </div>
                <div className="catalog-search">
                  <input
                    ref={searchInputRef}
                    type="search"
                    className="catalog-input"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Search modules or file paths… (Press '/' to focus)"
                    aria-label="Filter modules"
                  />
                  {query && (
                    <button className="button secondary" onClick={() => setQuery("")} type="button">
                      Clear
                    </button>
                  )}
                </div>
              </div>

              {state === "loading" && <div className="state-card"><span className="spinner" /><h2>Loading modules…</h2></div>}
              {state === "error" && <div className="state-card"><div className="empty-icon">!</div><h2>Could not load modules</h2><p>{error}</p></div>}
              {state === "ready" && filteredModules.length === 0 && (
                <div className="no-results">
                  <strong>No modules match your search</strong>
                  <span>Try a different query or clear the filter.</span>
                  {query && (
                    <button className="button secondary" style={{ marginTop: 8 }} onClick={() => setQuery("")} type="button">
                      Clear search
                    </button>
                  )}
                </div>
              )}
              {state === "ready" && filteredModules.length > 0 && (
                <div className="catalog-table-wrap">
                  <table className="catalog-table">
                    <thead>
                      <tr>
                        <th>Module Name</th>
                        <th>File Path</th>
                        <th style={{ width: 220, textAlign: "right" }}>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredModules.map((mod) => {
                        const loc = nodeLocation(mod);
                        return (
                          <tr key={mod.id}>
                            <td>
                              <strong>{mod.name}</strong>
                            </td>
                            <td>
                              <code>{loc ?? mod.path ?? "—"}</code>
                            </td>
                            <td style={{ textAlign: "right" }}>
                              <button
                                type="button"
                                className="inspect-btn"
                                onClick={() => inspectNodeOnGraph(mod.id)}
                                title={`Inspect ${mod.name} on graph`}
                              >
                                Inspect on Graph ↗
                              </button>
                              <button
                                type="button"
                                className="inspect-btn"
                                style={{ marginLeft: 6 }}
                                onClick={() => {
                                  setDrillDownNodeId(mod.id);
                                  setSelectedId(mod.id);
                                  setActiveView("architecture");
                                }}
                                title={`Drill into ${mod.name} scope`}
                              >
                                Drill In ↗
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
          )}
        </section>
        <aside className="inspector" aria-label="Node inspector">
          <div className="inspector-header"><span>INSPECTOR</span>{selected && <button className="close-button" onClick={() => { setSelectedId(null); setFocusDepth("all"); }} type="button" aria-label="Close inspector">×</button>}</div>
          {!selected ? <div className="inspector-empty"><div className="empty-icon small">◇</div><h2>Nothing selected</h2><p>Select a node in the graph to inspect its source, focus its neighborhood, and drill down.</p></div> : <div className="inspector-detail">
            <span className={`type-chip ${selected.type}`}>{TYPE_LABELS[selected.type]}</span>
            <h2>{selected.name}</h2>
            <div className="node-id-row">
              <p className="node-id">{selected.id}</p>
              <button
                type="button"
                className="copy-button"
                onClick={() => handleCopyId(selected.id)}
                title="Copy node ID to clipboard"
                aria-label="Copy node ID"
              >
                {copiedId ? "✓ Copied" : "Copy"}
              </button>
            </div>
            {nodeLocation(selected) && <div className="source-location">{nodeLocation(selected)}</div>}

            {/* Navigation & Focus Actions */}
            <div className="inspector-actions">
              <div className="action-row">
                <span className="action-label">Neighborhood Focus</span>
                <div className="button-group">
                  <button
                    type="button"
                    className={`mini-button ${focusDepth === 1 ? "active" : ""}`}
                    onClick={() => setFocusDepth(focusDepth === 1 ? "all" : 1)}
                    title="Focus 1-hop direct connections"
                  >
                    1-hop
                  </button>
                  <button
                    type="button"
                    className={`mini-button ${focusDepth === 2 ? "active" : ""}`}
                    onClick={() => setFocusDepth(focusDepth === 2 ? "all" : 2)}
                    title="Focus 2-hop neighborhood"
                  >
                    2-hop
                  </button>
                  <button
                    type="button"
                    className={`mini-button ${focusDepth === 3 ? "active" : ""}`}
                    onClick={() => setFocusDepth(focusDepth === 3 ? "all" : 3)}
                    title="Focus 3-hop neighborhood"
                  >
                    3-hop
                  </button>
                  {focusDepth !== "all" && (
                    <button
                      type="button"
                      className="mini-button secondary"
                      onClick={() => setFocusDepth("all")}
                      title="Reset focus to full graph"
                    >
                      Reset
                    </button>
                  )}
                </div>
              </div>

              {(selected.type === "package" || selected.type === "module") && (
                <div className="action-row">
                  <button
                    type="button"
                    className="button primary full-width"
                    onClick={() => setDrillDownNodeId(selected.id)}
                  >
                    Drill into {selected.type} ↗
                  </button>
                </div>
              )}

              {drillDownNodeId === selected.id && (
                <div className="action-row">
                  <button
                    type="button"
                    className="button secondary full-width"
                    onClick={() => setDrillDownNodeId(null)}
                  >
                    Exit {selected.type} drill-down
                  </button>
                </div>
              )}

              {selected.type === "package" && (
                <div className="action-row">
                  <button
                    type="button"
                    className="button secondary full-width"
                    onClick={() => {
                      const next = new Set(collapsedPackageIds);
                      if (next.has(selected.id)) {
                        next.delete(selected.id);
                      } else {
                        next.add(selected.id);
                      }
                      setCollapsedPackageIds(next);
                    }}
                  >
                    {collapsedPackageIds.has(selected.id) ? "Expand package contents" : "Collapse package contents"}
                  </button>
                </div>
              )}
            </div>

            {/* Architecture Intelligence / Explanation */}
            <section className="explanation-section" aria-label="Architecture Intelligence">
              <div className="section-header-row">
                <h3>Architecture Intelligence</h3>
                {!explanation && !explanationLoading && (
                  <button
                    type="button"
                    className="mini-button primary"
                    onClick={() => void requestExplanation(selected.id)}
                  >
                    Explain node
                  </button>
                )}
              </div>

              {explanationLoading && (
                <div className="explanation-status loading">
                  <span className="spinner small" /> Synthesizing structural insights…
                </div>
              )}

              {explanationError && (
                <div className="explanation-status error">
                  <p>{explanationError}</p>
                  <button
                    type="button"
                    className="mini-button secondary"
                    onClick={() => void requestExplanation(selected.id)}
                  >
                    Retry
                  </button>
                </div>
              )}

              {explanation && (
                <div className="explanation-card">
                  <div className="explanation-badges">
                    <span className="explanation-badge role">{explanation.role}</span>
                    <span className="explanation-badge provider">{explanation.provider}</span>
                  </div>
                  <p className="explanation-summary">{explanation.summary}</p>
                  <div className="explanation-block">
                    <h4>Impact</h4>
                    <p>{explanation.architectural_impact}</p>
                  </div>
                  <div className="explanation-block">
                    <h4>Dependencies</h4>
                    <p>{explanation.dependencies_summary}</p>
                  </div>
                  {explanation.recommendations.length > 0 && (
                    <div className="explanation-block">
                      <h4>Recommendations</h4>
                      <ul>
                        {explanation.recommendations.map((rec, idx) => (
                          <li key={idx}>{rec}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </section>

            <section><h3>Relationships <span>{selectedEdges.length}</span></h3>
{selectedEdges.length === 0 ? <p className="muted-copy">No static relationships recorded.</p> : <ul>{selectedEdges.map((edge, index) => { const relatedId = edge.source === selected.id ? edge.target : edge.source; const related = nodeMap.get(relatedId); return <li key={`${edge.source}-${edge.target}-${index}`}><button onClick={() => setSelectedId(relatedId)} type="button"><span>{edge.source === selected.id ? "→" : "←"} {edge.type}</span><strong>{related?.name ?? relatedId}</strong></button></li>; })}</ul>}</section>
            {Object.keys(selected.metadata).length > 0 && <section><h3>Metadata</h3><dl>{Object.entries(selected.metadata).map(([key, value]) => <div key={key}><dt>{key}</dt><dd>{typeof value === "string" ? value : JSON.stringify(value)}</dd></div>)}</dl></section>}
          </div>}
        </aside>
      </section>
    </main>
  );
}
