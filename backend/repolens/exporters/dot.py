"""Graphviz DOT exporter for architecture graphs."""

from __future__ import annotations

import re

from repolens.graph.engine import GraphEngine
from repolens.models.graph import NodeType


def _sanitize_id(node_id: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_]", "_", node_id)


class DotExporter:
    """Exports an architecture graph into Graphviz DOT syntax."""

    def export(self, graph: GraphEngine) -> str:
        lines: list[str] = [
            "digraph Architecture {",
            '  rankdir="LR";',
            '  node [fontname="Helvetica", fontsize=11, style="filled,rounded", shape="box"];',
            '  edge [fontname="Helvetica", fontsize=9];',
        ]

        for node in graph.document.nodes:
            nid = _sanitize_id(node.id)
            safe_name = node.name.replace('"', '\\"')
            if node.type == NodeType.ROUTE:
                lines.append(
                    f'  {nid} [label="{safe_name}", fillcolor="#d1fae5", '
                    'color="#10b981", shape="ellipse"];'
                )
            elif node.type == NodeType.MODEL:
                lines.append(
                    f'  {nid} [label="{safe_name}", fillcolor="#e0e7ff", '
                    'color="#6366f1", shape="cylinder"];'
                )
            elif node.type == NodeType.PACKAGE:
                lines.append(
                    f'  {nid} [label="{safe_name}", fillcolor="#fef3c7", '
                    'color="#f59e0b", shape="folder"];'
                )
            elif node.type == NodeType.COMPONENT:
                lines.append(
                    f'  {nid} [label="<{safe_name}>", fillcolor="#e0f2fe", color="#0284c7"];'
                )
            else:
                lines.append(
                    f'  {nid} [label="{safe_name}", fillcolor="#f4f4f5", color="#71717a"];'
                )

        for edge in graph.document.edges:
            src = _sanitize_id(edge.source)
            tgt = _sanitize_id(edge.target)
            etype = edge.type.value
            lines.append(f'  {src} -> {tgt} [label="{etype}"];')

        lines.append("}")
        return "\n".join(lines) + "\n"
