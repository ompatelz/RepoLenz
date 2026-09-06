from fastapi.testclient import TestClient

from repolens.api import create_app
from repolens.models import Edge, EdgeType, GraphDocument, Node, NodeType


def test_graph_endpoints_expose_read_only_document() -> None:
    document = GraphDocument(
        nodes=[
            Node(id="a", type=NodeType.MODULE, name="a"),
            Node(id="b", type=NodeType.MODULE, name="b"),
        ],
        edges=[Edge(source="a", target="b", type=EdgeType.IMPORTS)],
    )
    client = TestClient(create_app(document))

    assert client.get("/api/stats").json() == {
        "nodes": 2,
        "edges": 1,
        "cycles": 0,
        "routes": 0,
        "models": 0,
    }
    assert client.get("/api/nodes/a/neighbors").json()[0]["id"] == "b"
    assert client.get("/api/nodes/missing").status_code == 404


def test_graph_endpoint_supports_level_filter() -> None:
    document = GraphDocument(
        nodes=[
            Node(id="repository:demo", type=NodeType.REPOSITORY, name="demo"),
            Node(id="module:demo.main", type=NodeType.MODULE, name="main"),
            Node(id="symbol:demo.main:run", type=NodeType.FUNCTION, name="run"),
        ],
        edges=[
            Edge(source="repository:demo", target="module:demo.main", type=EdgeType.CONTAINS),
            Edge(source="module:demo.main", target="symbol:demo.main:run", type=EdgeType.CONTAINS),
        ],
    )
    client = TestClient(create_app(document))

    # Repository level
    repo_res = client.get("/api/graph?level=repository")
    assert repo_res.status_code == 200
    assert len(repo_res.json()["nodes"]) == 1
    assert repo_res.json()["nodes"][0]["type"] == "repository"

    # Module level
    module_res = client.get("/api/graph?level=module")
    assert module_res.status_code == 200
    assert len(module_res.json()["nodes"]) == 2
    assert {n["type"] for n in module_res.json()["nodes"]} == {"repository", "module"}

    # Full/symbol level
    all_res = client.get("/api/graph?level=symbol")
    assert all_res.status_code == 200
    assert len(all_res.json()["nodes"]) == 3

    # Invalid level
    invalid_res = client.get("/api/graph?level=invalid")
    assert invalid_res.status_code == 400
    assert "Invalid level" in invalid_res.json()["detail"]


def test_node_subgraph_endpoint_returns_bounded_neighborhood() -> None:
    document = GraphDocument(
        nodes=[
            Node(id="module:a", type=NodeType.MODULE, name="a"),
            Node(id="module:b", type=NodeType.MODULE, name="b"),
            Node(id="module:c", type=NodeType.MODULE, name="c"),
        ],
        edges=[
            Edge(source="module:a", target="module:b", type=EdgeType.IMPORTS),
            Edge(source="module:b", target="module:c", type=EdgeType.IMPORTS),
        ],
    )
    client = TestClient(create_app(document))

    # 1-hop from a reaches a and b
    one_hop = client.get("/api/nodes/module:a/subgraph?depth=1")
    assert one_hop.status_code == 200
    assert {n["id"] for n in one_hop.json()["nodes"]} == {"module:a", "module:b"}
    assert one_hop.json()["metadata"]["depth"] == 1
    assert one_hop.json()["metadata"]["focus"] == "module:a"

    # 2-hops from a reaches a, b, and c
    two_hop = client.get("/api/nodes/module:a/subgraph?depth=2")
    assert two_hop.status_code == 200
    assert {n["id"] for n in two_hop.json()["nodes"]} == {"module:a", "module:b", "module:c"}

    # Missing node returns 404
    assert client.get("/api/nodes/module:missing/subgraph").status_code == 404

    # Out of bounds depth (<1 or >5) returns 422
    assert client.get("/api/nodes/module:a/subgraph?depth=0").status_code == 422
    assert client.get("/api/nodes/module:a/subgraph?depth=6").status_code == 422
