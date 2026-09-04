import { useEffect, useState } from "react";

type ApiStats = { nodes: number; edges: number; cycles: number };

export function App() {
  const [stats, setStats] = useState<ApiStats | null>(null);

  useEffect(() => {
    fetch("/api/stats").then((response) => response.ok ? response.json() : null).then(setStats).catch(() => setStats(null));
  }, []);
  const cards = [
    { label: "Nodes", value: stats?.nodes ?? "—", detail: stats ? "Architecture elements" : "Awaiting analysis" },
    { label: "Relationships", value: stats?.edges ?? "—", detail: stats ? "Static evidence links" : "Awaiting analysis" },
    { label: "Cycles", value: stats?.cycles ?? "—", detail: stats ? "Dependency cycles" : "Awaiting analysis" },
    { label: "Status", value: stats ? "Ready" : "Local", detail: stats ? "API connected" : "Start repolens serve" },
  ];
  return (
    <main className="app-shell">
      <header className="topbar">
        <a className="brand" href="/" aria-label="RepoLens home">
          <span className="brand-mark" aria-hidden="true">⌘</span>
          <span>RepoLens</span>
          <span className="beta">LOCAL</span>
        </a>
        <div className="repository-picker" aria-label="Active repository">
          <span className="status-dot" />
          <span className="repo-name">No repository loaded</span>
          <kbd>⌘ K</kbd>
        </div>
        <div className="topbar-actions">
          <button className="button secondary" type="button">Open repository</button>
          <button className="button primary" type="button">Run analysis</button>
        </div>
      </header>

      <section className="workspace">
        <aside className="sidebar" aria-label="Project navigation">
          <div className="sidebar-heading">EXPLORER</div>
          <nav>
            <a className="nav-item active" href="#architecture"><span>◇</span> Architecture</a>
            <a className="nav-item" href="#modules"><span>□</span> Modules</a>
            <a className="nav-item" href="#symbols"><span>⌘</span> Symbols</a>
            <a className="nav-item" href="#frameworks"><span>◌</span> Frameworks</a>
          </nav>
          <div className="sidebar-footer">
            <div className="sidebar-heading">ANALYSIS</div>
            <div className="muted-line"><span className="status-dot muted" /> Waiting for a repository</div>
            <p>RepoLens reads code statically. Your repository is never executed.</p>
          </div>
        </aside>

        <section className="content" id="architecture">
          <div className="content-header">
            <div>
              <p className="eyebrow">ARCHITECTURE MAP</p>
              <h1>Understand the shape of your codebase.</h1>
            </div>
            <div className="view-controls" aria-label="Graph controls">
              <button className="icon-button" type="button" aria-label="Fit graph">⊙</button>
              <button className="icon-button" type="button" aria-label="Zoom out">−</button>
              <button className="icon-button" type="button" aria-label="Zoom in">+</button>
            </div>
          </div>

          <div className="stats-grid">
            {cards.map((stat) => (
              <article className="stat-card" key={stat.label}>
                <p>{stat.label}</p><strong>{stat.value}</strong><span>{stat.detail}</span>
              </article>
            ))}
          </div>

          <section className="graph-panel" aria-label="Architecture graph">
            <div className="graph-grid" />
            <div className="empty-state">
              <div className="empty-icon">⌘</div>
              <h2>Your architecture map will appear here</h2>
              <p>Choose a local repository, then run a safe static analysis to reveal modules, symbols, and their relationships.</p>
              <button className="button primary" type="button">Open a repository</button>
            </div>
            <div className="graph-legend"><span><i className="dot module" /> Module</span><span><i className="dot symbol" /> Symbol</span><span><i className="dot route" /> Route</span></div>
          </section>
        </section>

        <aside className="inspector" aria-label="Node inspector">
          <div className="inspector-header"><span>INSPECTOR</span><button className="close-button" type="button" aria-label="Close inspector">×</button></div>
          <div className="inspector-empty">
            <div className="empty-icon small">◇</div>
            <h2>Nothing selected</h2>
            <p>Select a node in the graph to inspect its source, relationships, and framework metadata.</p>
          </div>
        </aside>
      </section>
    </main>
  );
}
