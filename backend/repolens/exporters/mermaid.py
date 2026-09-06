"""Mermaid diagram exporter for architecture graphs."""

from __future__ import annotations

import re

from repolens.graph.engine import GraphEngine
from repolens.models.graph import NodeType


def _sanitize_id(node_id: str) -> str:
    """Turn arbitrary node id into a valid Mermaid identifier."""
    return re.sub(r"[^a-zA-Z0-9_]", "_", node_id)


class MermaidExporter:
    """Exports an architecture graph into Mermaid flowchart syntax."""

    def export(self, graph: GraphEngine) -> str:
        lines: list[str] = ["flowchart TD"]

        # 1. Define nodes
        for node in graph.document.nodes:
            nid = _sanitize_id(node.id)
            safe_name = node.name.replace('"', "'")
            if node.type == NodeType.ROUTE:
                lines.append(f'    {nid}(["{safe_name}"])')
            elif node.type == NodeType.MODEL:
                lines.append(f'    {nid}[("{safe_name}")]')
            elif node.type == NodeType.PACKAGE:
                lines.append(f'    {nid}{{"{safe_name}"}}')
            elif node.type == NodeType.COMPONENT:
                lines.append(f'    {nid}["&lt;{safe_name}&gt;"]')
            else:
                lines.append(f'    {nid}["{safe_name}"]')

        # 2. Define edges
        for edge in graph.document.edges:
            src = _sanitize_id(edge.source)
            tgt = _sanitize_id(edge.target)
            etype = edge.type.value
            lines.append(f"    {src} -->|{etype}| {tgt}")

        # 3. Add styling classes
        lines.append("    classDef route fill:#064e3b,stroke:#34d399,stroke-width:2px,color:#fff;")
        lines.append("    classDef model fill:#1e1b4b,stroke:#818cf8,stroke-width:2px,color:#fff;")
        lines.append(
            "    classDef component fill:#0c4a6e,stroke:#38bdf8,stroke-width:2px,color:#fff;"
        )
        lines.append(
            "    classDef package fill:#451a03,stroke:#fbbf24,stroke-width:2px,color:#fff;"
        )

        route_ids = [_sanitize_id(n.id) for n in graph.document.nodes if n.type == NodeType.ROUTE]
        if route_ids:
            lines.append(f"    class {','.join(route_ids)} route;")

        model_ids = [_sanitize_id(n.id) for n in graph.document.nodes if n.type == NodeType.MODEL]
        if model_ids:
            lines.append(f"    class {','.join(model_ids)} model;")

        comp_ids = [
            _sanitize_id(n.id) for n in graph.document.nodes if n.type == NodeType.COMPONENT
        ]
        if comp_ids:
            lines.append(f"    class {','.join(comp_ids)} component;")

        return "\n".join(lines) + "\n"
