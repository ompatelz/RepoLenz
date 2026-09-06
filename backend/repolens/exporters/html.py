"""Standalone self-contained HTML report exporter."""

from __future__ import annotations

import html

from repolens.graph.engine import GraphEngine


class HtmlReportExporter:
    """Exports a self-contained offline architecture report in a single HTML file."""

    def export(self, graph: GraphEngine) -> str:
        doc = graph.document
        stats = graph.stats()
        cycles = graph.cycles()
        repo_name = html.escape(str(doc.metadata.get("repository", "Codebase")))

        json_payload = html.escape(doc.model_dump_json())

        # Render Nodes Table
        nodes_rows = []
        for n in doc.nodes:
            loc = f"{n.path}:{n.line_start}" if n.path and n.line_start else (n.path or "—")
            nodes_rows.append(
                f"<tr><td><code>{html.escape(n.id)}</code></td>"
                f"<td><span class='type-badge {n.type.value}'>{n.type.value}</span></td>"
                f"<td><strong>{html.escape(n.name)}</strong></td>"
                f"<td>{html.escape(loc)}</td></tr>"
            )
        nodes_table_html = "\n".join(nodes_rows)

        # Render Edges Table
        edges_rows = []
        for e in doc.edges:
            edges_rows.append(
                f"<tr><td><code>{html.escape(e.source)}</code></td>"
                f"<td><code>{html.escape(e.type.value)}</code></td>"
                f"<td><code>{html.escape(e.target)}</code></td></tr>"
            )
        edges_table_html = "\n".join(edges_rows)

        cycles_banner = ""
        if cycles:
            cycle_items = "".join(
                f"<li>{' -> '.join(html.escape(c) for c in cycle)}</li>" for cycle in cycles
            )
            cycles_banner = (
                f"<div class='warning-box'><h3>⚠️ Circular Dependencies ({len(cycles)})</h3>"
                f"<ul>{cycle_items}</ul></div>"
            )

        css = """
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
           background: #0c0c0e; color: #e4e4e7; margin: 0; padding: 24px; }
    h1, h2, h3 { color: #fafafa; }
    .header { border-bottom: 1px solid #27272a; padding-bottom: 16px; margin-bottom: 24px; }
    .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
                 gap: 16px; margin-bottom: 24px; }
    .stat-card { background: #18181b; border: 1px solid #27272a;
                 border-radius: 8px; padding: 16px; }
    .stat-card p { margin: 0 0 8px 0; font-size: 11px; color: #a1a1aa; text-transform: uppercase; }
    .stat-card strong { font-size: 24px; color: #fafafa; }
    .warning-box { background: #451a03; border: 1px solid #f59e0b; border-radius: 8px;
                   padding: 16px; margin-bottom: 24px; }
    table { width: 100%; border-collapse: collapse; margin-bottom: 32px; background: #18181b;
            border-radius: 8px; overflow: hidden; border: 1px solid #27272a; }
    th, td { padding: 10px 14px; text-align: left;
             border-bottom: 1px solid #27272a; font-size: 13px; }

    th { background: #27272a; color: #d4d4d8; font-size: 11px; text-transform: uppercase; }
    code { background: #27272a; padding: 2px 6px; border-radius: 4px; font-family: monospace; }
    .type-badge { font-size: 10px; font-weight: 700; text-transform: uppercase;
                  padding: 2px 6px; border-radius: 4px; }
    .type-badge.route { background: #064e3b; color: #6ee7b7; }
    .type-badge.model { background: #312e81; color: #a5b4fc; }
    .type-badge.module { background: #1e293b; color: #94a3b8; }
    .type-badge.component { background: #0c4a6e; color: #7dd3fc; }
    .type-badge.package { background: #451a03; color: #fcd34d; }
"""

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>RepoLens Architecture Report - {repo_name}</title>
  <style>{css}  </style>
</head>
<body>
  <div class="header">
    <h1>RepoLens Architecture Snapshot: {repo_name}</h1>
    <p>Generated statically with zero runtime target code execution.</p>
  </div>

  <div class="stats-grid">
    <div class="stat-card"><p>Nodes</p><strong>{stats.get("nodes", 0)}</strong></div>
    <div class="stat-card"><p>Relationships</p><strong>{stats.get("edges", 0)}</strong></div>
    <div class="stat-card"><p>Routes</p><strong>{stats.get("routes", 0)}</strong></div>
    <div class="stat-card"><p>Models</p><strong>{stats.get("models", 0)}</strong></div>
    <div class="stat-card"><p>Cycles</p><strong>{stats.get("cycles", 0)}</strong></div>
  </div>

  {cycles_banner}

  <h2>Architecture Elements ({len(doc.nodes)})</h2>
  <table>
    <thead><tr><th>ID</th><th>Type</th><th>Name</th><th>Location</th></tr></thead>
    <tbody>{nodes_table_html}</tbody>
  </table>

  <h2>Directed Relationships ({len(doc.edges)})</h2>
  <table>
    <thead><tr><th>Source</th><th>Type</th><th>Target</th></tr></thead>
    <tbody>{edges_table_html}</tbody>
  </table>

  <script id="repolens-data" type="application/json">{json_payload}</script>
</body>
</html>
"""
