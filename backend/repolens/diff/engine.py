"""Engine for comparing and diffing two architecture graphs."""

from __future__ import annotations

from repolens.diff.models import (
    DiffStatus,
    EdgeDiff,
    GraphDiffReport,
    NodeDiff,
)
from repolens.graph.engine import GraphEngine
from repolens.models.graph import NodeType


def compute_graph_diff(base: GraphEngine, target: GraphEngine) -> GraphDiffReport:
    """Compare base and target architecture graphs, detecting changes and regressions."""
    base_nodes = {n.id: n for n in base.document.nodes}
    target_nodes = {n.id: n for n in target.document.nodes}

    base_edges = {(e.source, e.target, e.type.value): e for e in base.document.edges}
    target_edges = {(e.source, e.target, e.type.value): e for e in target.document.edges}

    # Added and removed nodes
    added_nodes = [
        NodeDiff(node_id=nid, name=n.name, type=n.type, status=DiffStatus.ADDED)
        for nid, n in target_nodes.items()
        if nid not in base_nodes
    ]
    removed_nodes = [
        NodeDiff(node_id=nid, name=n.name, type=n.type, status=DiffStatus.REMOVED)
        for nid, n in base_nodes.items()
        if nid not in target_nodes
    ]

    # Added and removed edges
    added_edges = [
        EdgeDiff(source=s, target=t, type=typ, status=DiffStatus.ADDED)
        for (s, t, typ) in target_edges
        if (s, t, typ) not in base_edges
    ]
    removed_edges = [
        EdgeDiff(source=s, target=t, type=typ, status=DiffStatus.REMOVED)
        for (s, t, typ) in base_edges
        if (s, t, typ) not in target_edges
    ]

    # Cycle regression detection
    base_cycles = {tuple(sorted(c)) for c in base.cycles()}
    target_cycles = target.cycles()
    new_cycles = [c for c in target_cycles if tuple(sorted(c)) not in base_cycles]

    # Route breaking change detection (routes in base that no longer exist in target)
    broken_routes = [
        n.name
        for nid, n in base_nodes.items()
        if n.type == NodeType.ROUTE and nid not in target_nodes
    ]

    has_breaking = len(new_cycles) > 0 or len(broken_routes) > 0

    base_name = str(base.document.metadata.get("repository", "Base"))
    target_name = str(target.document.metadata.get("repository", "Target"))

    summary = (
        f"Architecture Diff ({base_name} -> {target_name}): "
        f"+{len(added_nodes)}/-{len(removed_nodes)} nodes, "
        f"+{len(added_edges)}/-{len(removed_edges)} edges. "
        f"New cycles: {len(new_cycles)}, Removed routes: {len(broken_routes)}."
    )

    return GraphDiffReport(
        base_repository=base_name,
        target_repository=target_name,
        added_nodes=added_nodes,
        removed_nodes=removed_nodes,
        added_edges=added_edges,
        removed_edges=removed_edges,
        new_cycles=new_cycles,
        broken_routes=broken_routes,
        has_breaking_changes=has_breaking,
        summary=summary,
    )
