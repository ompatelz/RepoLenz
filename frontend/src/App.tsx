import { useCallback, useEffect, useMemo, useState } from "react";

type NodeType = "repository" | "package" | "module" | "class" | "function" | "method" | "route" | "model" | "dependency";
type GraphNode = { id: string; type: NodeType; name: string; path: string | null; line_start: number | null; line_end: number | null; metadata: Record<string, unknown> };
type GraphEdge = { source: string; target: string; type: string };
type GraphDocument = { metadata: Record<string, unknown>; nodes: GraphNode[]; edges: GraphEdge[] };
type ApiStats = { nodes: number; edges: number; cycles: number };
type LoadState = "loading" | "ready" | "error";

const TYPE_LABELS: Record<NodeType, string> = { repository: "Repository", package: "Package", module: "Module", class: "Class", function: "Function", method: "Method", route: "Route", model: "Model", dependency: "Dependency" };

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
  const [query, setQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState<NodeType | "all">("all");
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setState("loading"); setError(null);
    try {
      const [nextGraph, nextStats] = await Promise.all([getJson<GraphDocument>("/api/graph"), getJson<ApiStats>("/api/stats")]);
      setGraph(nextGraph); setStats(nextStats);
      setSelectedId((current) => current && nextGraph.nodes.some((node) => node.id === current) ? current : null);
      setState("ready");
    } catch (caught) {
      setGraph(null); setStats(null); setState("error");
      setError(caught instanceof Error ? caught.message : "Could not contact the RepoLens API.");
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const nodeTypes = useMemo(() => new Set(graph?.nodes.map((node) => node.type) ?? []), [graph]);
  const visibleNodes = useMemo(() => {
    const normalized = query.trim().toLocaleLowerCase();
    return (graph?.nodes ?? []).filter((node) => {
      const matchesType = typeFilter === "all" || node.type === typeFilter;
      const matchesQuery = !normalized || [node.name, node.path, node.type].filter(Boolean).some((value) => value?.toLocaleLowerCase().includes(normalized));
      return matchesType && matchesQuery;
    });
  }, [graph, query, typeFilter]);
  const selected = graph?.nodes.find((node) => node.id === selectedId) ?? null;
  const selectedEdges = useMemo(() => (graph?.edges ?? []).filter((edge) => edge.source === selectedId || edge.target === selectedId), [graph, selectedId]);
  const cards = [
    { label: "Nodes", value: stats?.nodes ?? "—", detail: "Architecture elements" },
    { label: "Relationships", value: stats?.edges ?? "—", detail: "Static evidence links" },
    { label: "Cycles", value: stats?.cycles ?? "—", detail: "Dependency cycles" },
    { label: "Visible", value: state === "ready" ? visibleNodes.length : "—", detail: "Current map filter" },
  ];
  const repositoryName = typeof graph?.metadata.name === "string" ? graph.metadata.name : "Local repository";

  return <main className="app-shell">
    <header className="topbar"><a className="brand" href="/" aria-label="RepoLens home"><span className="brand-mark" aria-hidden="true">⌘</span><span>RepoLens</span><span className="beta">LOCAL</span></a><div className="repository-picker" aria-label="Active repository"><span className={`status-dot ${state === "ready" ? "" : "muted"}`} /><span className="repo-name">{state === "ready" ? repositoryName : "No repository loaded"}</span></div><div className="topbar-actions"><button className="button secondary" onClick={() => void load()} type="button">Refresh</button></div></header>
    <section className="workspace">
      <aside className="sidebar" aria-label="Project navigation"><div className="sidebar-heading">EXPLORER</div><nav><a className="nav-item active" href="#architecture"><span>◇</span> Architecture</a><a className="nav-item" href="#map"><span>□</span> Node map <b>{stats?.nodes ?? 0}</b></a><a className="nav-item" href="#modules"><span>⌘</span> Modules <b>{graph?.nodes.filter((node) => node.type === "module").length ?? 0}</b></a></nav><div className="sidebar-footer"><div className="sidebar-heading">ANALYSIS</div><div className="muted-line"><span className={`status-dot ${state === "ready" ? "" : "muted"}`} /> {state === "ready" ? "Static analysis ready" : "Waiting for local API"}</div><p>RepoLens reads code statically. Your repository is never executed.</p></div></aside>
      <section className="content" id="architecture"><div className="content-header"><div><p className="eyebrow">ARCHITECTURE MAP</p><h1>Understand the shape of your codebase.</h1></div><button className="button secondary" onClick={() => setSelectedId(null)} type="button" disabled={!selected}>Clear selection</button></div><div className="stats-grid">{cards.map((stat) => <article className="stat-card" key={stat.label}><p>{stat.label}</p><strong>{stat.value}</strong><span>{stat.detail}</span></article>)}</div>
        <section className="graph-panel" id="map" aria-label="Architecture graph"><div className="graph-grid" />
          {state === "loading" && <div className="state-card"><span className="spinner" /><h2>Loading architecture map</h2><p>Reading the local analysis API…</p></div>}
          {state === "error" && <div className="state-card"><div className="empty-icon">!</div><h2>Could not load the map</h2><p>{error ?? "Start RepoLens with repolens serve &lt;path&gt;, then refresh."}</p><button className="button primary" onClick={() => void load()} type="button">Try again</button></div>}
          {state === "ready" && graph && graph.nodes.length === 0 && <div className="state-card"><div className="empty-icon">◇</div><h2>No architecture nodes found</h2><p>This analysis did not produce graph nodes. Try a repository containing Python source files.</p></div>}
          {state === "ready" && graph && graph.nodes.length > 0 && <div className="map-content"><div className="map-toolbar"><label><span className="sr-only">Search nodes</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search names, paths, or types…" /></label><select value={typeFilter} onChange={(event) => setTypeFilter(event.target.value as NodeType | "all")} aria-label="Filter by node type"><option value="all">All node types</option>{Object.entries(TYPE_LABELS).filter(([type]) => nodeTypes.has(type as NodeType)).map(([type, label]) => <option key={type} value={type}>{label}</option>)}</select></div>{visibleNodes.length === 0 ? <div className="no-results"><strong>No matching nodes</strong><span>Try clearing the search or type filter.</span></div> : <div className="node-map" role="list" aria-label="Architecture nodes">{visibleNodes.map((node) => <button className={`graph-node ${node.type} ${selectedId === node.id ? "selected" : ""}`} onClick={() => setSelectedId(node.id)} type="button" key={node.id} role="listitem"><span className="node-type">{TYPE_LABELS[node.type]}</span><strong>{node.name}</strong>{node.path && <small title={nodeLocation(node) ?? undefined}>{nodeLocation(node)}</small>}</button>)}</div>}</div>}
          <div className="graph-legend"><span><i className="dot module" /> Module</span><span><i className="dot symbol" /> Symbol</span><span><i className="dot route" /> Route</span></div></section></section>
      <aside className="inspector" aria-label="Node inspector"><div className="inspector-header"><span>INSPECTOR</span>{selected && <button className="close-button" onClick={() => setSelectedId(null)} type="button" aria-label="Close inspector">×</button>}</div>{!selected ? <div className="inspector-empty"><div className="empty-icon small">◇</div><h2>Nothing selected</h2><p>Select a node in the map to inspect its source and relationships.</p></div> : <div className="inspector-detail"><span className={`type-chip ${selected.type}`}>{TYPE_LABELS[selected.type]}</span><h2>{selected.name}</h2><p className="node-id">{selected.id}</p>{nodeLocation(selected) && <div className="source-location">{nodeLocation(selected)}</div>}<section><h3>Relationships <span>{selectedEdges.length}</span></h3>{selectedEdges.length === 0 ? <p className="muted-copy">No static relationships recorded.</p> : <ul>{selectedEdges.map((edge, index) => { const relatedId = edge.source === selected.id ? edge.target : edge.source; const related = graph?.nodes.find((node) => node.id === relatedId); return <li key={`${edge.source}-${edge.target}-${index}`}><button onClick={() => setSelectedId(relatedId)} type="button"><span>{edge.source === selected.id ? "→" : "←"} {edge.type}</span><strong>{related?.name ?? relatedId}</strong></button></li>; })}</ul>}</section>{Object.keys(selected.metadata).length > 0 && <section><h3>Metadata</h3><dl>{Object.entries(selected.metadata).map(([key, value]) => <div key={key}><dt>{key}</dt><dd>{typeof value === "string" ? value : JSON.stringify(value)}</dd></div>)}</dl></section>}</div>}</aside>
    </section>
  </main>;
}
