import { useCallback, useEffect, useMemo, useState } from "react";

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

export function App() {
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

  const drillDownNode = useMemo(
    () => (drillDownNodeId ? graph?.nodes.find((n) => n.id === drillDownNodeId) ?? null : null),
    [drillDownNodeId, graph],
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
    const normalized = query.trim().toLocaleLowerCase();
    return processedGraph.nodes.filter((node) => {
      const matchesType = typeFilter === "all" || node.type === typeFilter;
      const matchesQuery =
        !normalized ||
        [node.name, node.path, node.type]
          .filter(Boolean)
          .some((value) => value?.toLocaleLowerCase().includes(normalized));
      return matchesType && matchesQuery;
    });
  }, [processedGraph.nodes, query, typeFilter]);

  const selected = graph?.nodes.find((node) => node.id === selectedId) ?? null;
  const selectedEdges = useMemo(
    () => (graph?.edges ?? []).filter((edge) => edge.source === selectedId || edge.target === selectedId),
    [graph, selectedId],
  );

  const cards = [
    { label: "Nodes", value: stats?.nodes ?? "—", detail: "Architecture elements" },
    { label: "Relationships", value: stats?.edges ?? "—", detail: "Static evidence links" },
    { label: "Cycles", value: stats?.cycles ?? "—", detail: "Dependency cycles" },
    { label: "Visible", value: state === "ready" ? visibleNodes.length : "—", detail: "Current map filter" },
  ];
  const repositoryName =
    typeof graph?.metadata.repository === "string" ? graph.metadata.repository : "Local repository";

  const handleNodeDoubleClick = (nodeId: string) => {
    const targetNode = graph?.nodes.find((n) => n.id === nodeId);
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
          <nav>
            <a className="nav-item active" href="#architecture"><span>◇</span> Architecture</a>
            <a className="nav-item" href="#map"><span>□</span> Graph <b>{stats?.nodes ?? 0}</b></a>
            <a className="nav-item" href="#modules"><span>⌘</span> Modules <b>{graph?.nodes.filter((node) => node.type === "module").length ?? 0}</b></a>
            <a className="nav-item" href="#routes"><span>⚡</span> Routes <b>{graph?.nodes.filter((node) => node.type === "route").length ?? 0}</b></a>
            <a className="nav-item" href="#models"><span>⛁</span> Models <b>{graph?.nodes.filter((node) => node.type === "model").length ?? 0}</b></a>
          </nav>
          <div className="sidebar-footer">
            <div className="sidebar-heading">ANALYSIS</div>
            <div className="muted-line"><span className={`status-dot ${state === "ready" ? "" : "muted"}`} /> {state === "ready" ? "Static analysis ready" : "Waiting for local API"}</div>
            <p>RepoLens reads code statically. Your repository is never executed.</p>
          </div>
        </aside>
        <section className="content" id="architecture">
          <div className="content-header">
            <div><p className="eyebrow">ARCHITECTURE MAP</p><h1>Understand the shape of your codebase.</h1></div>
            <div className="header-actions">
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
          <section className="graph-panel" id="map" aria-label="Architecture graph">
            {state === "loading" && <div className="state-card"><span className="spinner" /><h2>Loading architecture map</h2><p>Reading the local analysis API…</p></div>}
            {state === "error" && <div className="state-card"><div className="empty-icon">!</div><h2>Could not load the map</h2><p>{error ?? "Start RepoLens with repolens serve <path>, then refresh."}</p><button className="button primary" onClick={() => void load(level)} type="button">Try again</button></div>}
            {state === "ready" && graph && graph.nodes.length === 0 && <div className="state-card"><div className="empty-icon">◇</div><h2>No architecture nodes found</h2><p>This level or analysis produced no graph nodes. Try switching to "All" or a repository with Python source files.</p><button className="button secondary" onClick={() => handleLevelChange("all")} type="button">Switch to All</button></div>}
            {state === "ready" && graph && graph.nodes.length > 0 && <div className="graph-workspace">
              {/* Breadcrumb Navigation Bar */}
              <nav className="breadcrumbs-bar" aria-label="Hierarchy breadcrumbs">
                <span className="breadcrumbs-label">Scope:</span>
                {breadcrumbs.map((crumb, index) => (
                  <span key={crumb.id ?? "root"} className="breadcrumb-segment">
                    {index > 0 && <span className="breadcrumb-sep">/</span>}
                    <button
                      type="button"
                      className={`breadcrumb-btn ${crumb.id === drillDownNodeId ? "current" : ""}`}
                      onClick={() => setDrillDownNodeId(crumb.id)}
                      title={`Navigate to ${crumb.label}`}
                    >
                      {crumb.kind && <span className={`crumb-kind ${crumb.kind}`}>{crumb.kind}</span>}
                      {crumb.label}
                    </button>
                  </span>
                ))}
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

              <div className="map-toolbar">
                {/* Level Selector Tabs */}
                <div className="level-tabs" role="tablist" aria-label="Architecture hierarchy levels">
                  <button
                    type="button"
                    role="tab"
                    aria-selected={level === "all"}
                    className={`level-tab ${level === "all" ? "active" : ""}`}
                    onClick={() => handleLevelChange("all")}
                  >
                    All
                  </button>
                  <button
                    type="button"
                    role="tab"
                    aria-selected={level === "repository"}
                    className={`level-tab ${level === "repository" ? "active" : ""}`}
                    onClick={() => handleLevelChange("repository")}
                  >
                    Repo
                  </button>
                  <button
                    type="button"
                    role="tab"
                    aria-selected={level === "module"}
                    className={`level-tab ${level === "module" ? "active" : ""}`}
                    onClick={() => handleLevelChange("module")}
                  >
                    Modules
                  </button>
                  <button
                    type="button"
                    role="tab"
                    aria-selected={level === "symbol"}
                    className={`level-tab ${level === "symbol" ? "active" : ""}`}
                    onClick={() => handleLevelChange("symbol")}
                  >
                    Symbols
                  </button>
                </div>

                <label><span className="sr-only">Search nodes</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search names, paths, or types…" /></label>

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
        </section>
        <aside className="inspector" aria-label="Node inspector">
          <div className="inspector-header"><span>INSPECTOR</span>{selected && <button className="close-button" onClick={() => { setSelectedId(null); setFocusDepth("all"); }} type="button" aria-label="Close inspector">×</button>}</div>
          {!selected ? <div className="inspector-empty"><div className="empty-icon small">◇</div><h2>Nothing selected</h2><p>Select a node in the graph to inspect its source, focus its neighborhood, and drill down.</p></div> : <div className="inspector-detail">
            <span className={`type-chip ${selected.type}`}>{TYPE_LABELS[selected.type]}</span><h2>{selected.name}</h2><p className="node-id">{selected.id}</p>
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

            <section><h3>Relationships <span>{selectedEdges.length}</span></h3>{selectedEdges.length === 0 ? <p className="muted-copy">No static relationships recorded.</p> : <ul>{selectedEdges.map((edge, index) => { const relatedId = edge.source === selected.id ? edge.target : edge.source; const related = graph?.nodes.find((node) => node.id === relatedId); return <li key={`${edge.source}-${edge.target}-${index}`}><button onClick={() => setSelectedId(relatedId)} type="button"><span>{edge.source === selected.id ? "→" : "←"} {edge.type}</span><strong>{related?.name ?? relatedId}</strong></button></li>; })}</ul>}</section>
            {Object.keys(selected.metadata).length > 0 && <section><h3>Metadata</h3><dl>{Object.entries(selected.metadata).map(([key, value]) => <div key={key}><dt>{key}</dt><dd>{typeof value === "string" ? value : JSON.stringify(value)}</dd></div>)}</dl></section>}
          </div>}
        </aside>
      </section>
    </main>
  );
}
