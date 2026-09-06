"""Context extraction for bounded node architecture explanations."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from repolens.ai.models import NodeExplanationContext
from repolens.graph.engine import GraphEngine
from repolens.models.graph import NodeType


def extract_bounded_snippet(
    repo_root: Path | None,
    relative_path: str | None,
    line_start: int | None = None,
    line_end: int | None = None,
    max_lines: int = 60,
) -> str | None:
    """Safely extract a bounded source snippet without reading arbitrary filesystem data."""
    if repo_root is None or not relative_path:
        return None

    try:
        root = repo_root.resolve()
        target = (root / relative_path).resolve()
        # Security: verify path is strictly inside the repository root
        if not target.is_relative_to(root):
            return None
        if not target.is_file():
            return None
        # Avoid reading excessively large files or binaries
        if target.stat().st_size > 2 * 1024 * 1024:
            return None

        # Read only needed lines safely
        with target.open("r", encoding="utf-8", errors="replace") as file:
            all_lines = file.readlines()

        if not all_lines:
            return None

        if line_start is not None and line_start > 0:
            start_idx = line_start - 1
            if line_end is not None and line_end >= line_start:
                end_idx = min(line_end, start_idx + max_lines)
            else:
                end_idx = min(len(all_lines), start_idx + max_lines)
            selected = all_lines[start_idx:end_idx]
        else:
            selected = all_lines[:max_lines]

        snippet = "".join(selected).rstrip()
        return snippet if snippet else None
    except OSError:
        return None


def build_node_context(
    graph: GraphEngine,
    node_id: str,
    repo_root: Path | None = None,
    max_snippet_lines: int = 60,
) -> NodeExplanationContext:
    """Build bounded architectural context for an explanation request.

    Extracts:
    - Selected node metadata
    - 1-hop neighbor nodes
    - Incoming and outgoing edges
    - Related framework route and model metadata
    - Bounded source code snippet (up to max_snippet_lines)
    """
    node = graph.node(node_id)
    if node is None:
        raise KeyError(f"Node '{node_id}' not found in architecture graph.")

    neighbors = graph.neighbors(node_id, direction="both")
    incoming_edges = [edge for edge in graph.document.edges if edge.target == node_id]
    outgoing_edges = [edge for edge in graph.document.edges if edge.source == node_id]

    # Collect framework routes and models from node and neighbors
    framework_routes: list[dict[str, Any]] = []
    framework_models: list[dict[str, Any]] = []

    candidates = [node] + neighbors
    for item in candidates:
        if item.type == NodeType.ROUTE or "route" in item.metadata:
            route_info = {"id": item.id, "name": item.name, **item.metadata}
            if route_info not in framework_routes:
                framework_routes.append(route_info)
        if item.type == NodeType.MODEL or "table_name" in item.metadata:
            model_info = {"id": item.id, "name": item.name, **item.metadata}
            if model_info not in framework_models:
                framework_models.append(model_info)

    snippet = extract_bounded_snippet(
        repo_root=repo_root,
        relative_path=node.path,
        line_start=node.line_start,
        line_end=node.line_end,
        max_lines=max_snippet_lines,
    )

    repo_name = (
        graph.document.metadata.get("repository", "Repository")
        if isinstance(graph.document.metadata.get("repository"), str)
        else "Repository"
    )

    return NodeExplanationContext(
        node=node,
        neighbors=neighbors,
        incoming_edges=incoming_edges,
        outgoing_edges=outgoing_edges,
        source_snippet=snippet,
        repository_name=repo_name,
        framework_routes=framework_routes,
        framework_models=framework_models,
    )
