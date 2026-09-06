"""PlantUML diagram exporter for architecture graphs."""

from __future__ import annotations

import re

from repolens.graph.engine import GraphEngine
from repolens.models.graph import NodeType


def _sanitize_id(node_id: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_]", "_", node_id)


class PlantUmlExporter:
    """Exports an architecture graph into PlantUML component syntax."""

    def export(self, graph: GraphEngine) -> str:
        lines: list[str] = [
            "@startuml",
            "!theme plain",
            "skinparam componentStyle uml2",
            "skinparam defaultFontName sans-serif",
        ]

        # Nodes
        for node in graph.document.nodes:
            nid = _sanitize_id(node.id)
            safe_name = node.name.replace('"', "'")
            if node.type == NodeType.ROUTE:
                lines.append(f'boundary "{safe_name}" as {nid}')
            elif node.type == NodeType.MODEL:
                lines.append(f'database "{safe_name}" as {nid}')
            elif node.type == NodeType.PACKAGE:
                lines.append(f'package "{safe_name}" as {nid} {{}}')
            else:
                lines.append(f"component [{safe_name}] as {nid}")

        # Edges
        for edge in graph.document.edges:
            src = _sanitize_id(edge.source)
            tgt = _sanitize_id(edge.target)
            etype = edge.type.value
            lines.append(f"{src} ..> {tgt} : {etype}")

        lines.append("@enduml")
        return "\n".join(lines) + "\n"
