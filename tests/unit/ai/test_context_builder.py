from pathlib import Path

import pytest

from repolens.ai.context import build_node_context, extract_bounded_snippet
from repolens.graph.engine import GraphEngine
from repolens.models.graph import Edge, EdgeType, GraphDocument, Node, NodeType


def test_extract_bounded_snippet(tmp_path: Path) -> None:
    sample_file = tmp_path / "src" / "service.py"
    sample_file.parent.mkdir(parents=True, exist_ok=True)
    sample_file.write_text("\n".join(f"line_{i}" for i in range(1, 101)), encoding="utf-8")

    # Extract slice 10..20
    snippet = extract_bounded_snippet(tmp_path, "src/service.py", line_start=10, line_end=20)
    assert snippet is not None
    lines = snippet.splitlines()
    assert len(lines) == 11
    assert lines[0] == "line_10"
    assert lines[-1] == "line_20"

    # Enforces max lines cap
    capped_snippet = extract_bounded_snippet(
        tmp_path, "src/service.py", line_start=1, line_end=100, max_lines=15
    )
    assert capped_snippet is not None
    assert len(capped_snippet.splitlines()) == 15

    # Safe against directory traversal
    assert extract_bounded_snippet(tmp_path, "../outside.py") is None

    # Safe on non-existent file
    assert extract_bounded_snippet(tmp_path, "does_not_exist.py") is None


def test_build_node_context_extracts_bounds_and_neighbors(tmp_path: Path) -> None:
    repo_file = tmp_path / "app.py"
    repo_file.write_text("def index():\n    return {'hello': 'world'}\n", encoding="utf-8")

    document = GraphDocument(
        nodes=[
            Node(
                id="module:app",
                type=NodeType.MODULE,
                name="app",
                path="app.py",
                line_start=1,
                line_end=2,
            ),
            Node(
                id="route:app.index", type=NodeType.ROUTE, name="GET /", metadata={"method": "GET"}
            ),
            Node(id="module:utils", type=NodeType.MODULE, name="utils", path="utils.py"),
        ],
        edges=[
            Edge(source="module:app", target="route:app.index", type=EdgeType.EXPOSES),
            Edge(source="module:app", target="module:utils", type=EdgeType.IMPORTS),
        ],
        metadata={"repository": "demo_repo"},
    )
    graph = GraphEngine(document)

    context = build_node_context(graph, "module:app", repo_root=tmp_path)
    assert context.node.id == "module:app"
    assert context.repository_name == "demo_repo"
    assert len(context.neighbors) == 2
    assert len(context.outgoing_edges) == 2
    assert len(context.incoming_edges) == 0
    assert len(context.framework_routes) == 1
    assert context.source_snippet is not None
    assert "def index():" in context.source_snippet


def test_build_node_context_missing_node_raises() -> None:
    document = GraphDocument(nodes=[], edges=[])
    graph = GraphEngine(document)
    with pytest.raises(KeyError, match="not found"):
        build_node_context(graph, "missing_node")
