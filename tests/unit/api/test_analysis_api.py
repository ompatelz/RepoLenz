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

    assert client.get("/api/stats").json() == {"nodes": 2, "edges": 1, "cycles": 0}
    assert client.get("/api/nodes/a/neighbors").json()[0]["id"] == "b"
    assert client.get("/api/nodes/missing").status_code == 404
