from repolens.diff.engine import compute_graph_diff
from repolens.graph.engine import GraphEngine
from repolens.models.graph import Edge, EdgeType, GraphDocument, Node, NodeType


def test_diff_engine_detects_additions_and_removals() -> None:
    base_doc = GraphDocument(
        nodes=[
            Node(id="module:users", type=NodeType.MODULE, name="users"),
            Node(id="route:old_users", type=NodeType.ROUTE, name="GET /users"),
        ],
        edges=[
            Edge(source="module:users", target="route:old_users", type=EdgeType.EXPOSES),
        ],
        metadata={"repository": "base_v1"},
    )

    target_doc = GraphDocument(
        nodes=[
            Node(id="module:users", type=NodeType.MODULE, name="users"),
            Node(id="module:billing", type=NodeType.MODULE, name="billing"),
            Node(id="route:new_users", type=NodeType.ROUTE, name="GET /api/v2/users"),
        ],
        edges=[
            Edge(source="module:users", target="module:billing", type=EdgeType.IMPORTS),
            Edge(source="module:users", target="route:new_users", type=EdgeType.EXPOSES),
        ],
        metadata={"repository": "target_v2"},
    )

    report = compute_graph_diff(GraphEngine(base_doc), GraphEngine(target_doc))

    # Node diffs
    assert len(report.added_nodes) == 2  # billing, new_users
    assert any(n.node_id == "module:billing" for n in report.added_nodes)
    assert len(report.removed_nodes) == 1  # old_users
    assert report.removed_nodes[0].node_id == "route:old_users"

    # Edge diffs
    assert any(e.target == "module:billing" for e in report.added_edges)
    assert any(e.target == "route:old_users" for e in report.removed_edges)

    # Breaking changes: route:old_users was removed!
    assert report.has_breaking_changes is True
    assert "GET /users" in report.broken_routes


def test_diff_engine_detects_new_cycles() -> None:
    base_doc = GraphDocument(
        nodes=[
            Node(id="module:a", type=NodeType.MODULE, name="a"),
            Node(id="module:b", type=NodeType.MODULE, name="b"),
        ],
        edges=[
            Edge(source="module:a", target="module:b", type=EdgeType.IMPORTS),
        ],
    )

    target_doc = GraphDocument(
        nodes=[
            Node(id="module:a", type=NodeType.MODULE, name="a"),
            Node(id="module:b", type=NodeType.MODULE, name="b"),
        ],
        edges=[
            Edge(source="module:a", target="module:b", type=EdgeType.IMPORTS),
            Edge(source="module:b", target="module:a", type=EdgeType.IMPORTS),  # new cycle!
        ],
    )

    report = compute_graph_diff(GraphEngine(base_doc), GraphEngine(target_doc))
    assert len(report.new_cycles) == 1
    assert report.has_breaking_changes is True
