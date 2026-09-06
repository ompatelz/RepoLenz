from fastapi.testclient import TestClient

from repolens.api import create_app
from repolens.models import Edge, EdgeType, GraphDocument, Node, NodeType


def test_explain_endpoint_returns_explanation() -> None:
    document = GraphDocument(
        nodes=[
            Node(id="module:main", type=NodeType.MODULE, name="main", path="main.py"),
            Node(id="module:helper", type=NodeType.MODULE, name="helper", path="helper.py"),
        ],
        edges=[
            Edge(source="module:main", target="module:helper", type=EdgeType.IMPORTS),
        ],
        metadata={"repository": "test_service"},
    )
    client = TestClient(create_app(document))

    # POST explain endpoint with default offline provider
    res = client.post("/api/nodes/module:main/explain")
    assert res.status_code == 200
    data = res.json()
    assert data["node_id"] == "module:main"
    assert data["provider"] == "offline"
    assert "main" in data["summary"]
    assert "role" in data
    assert "architectural_impact" in data
    assert isinstance(data["recommendations"], list)

    # GET explain endpoint with mock provider
    get_res = client.get("/api/nodes/module:helper/explain?provider=mock")
    assert get_res.status_code == 200
    assert get_res.json()["provider"] == "mock"

    # Non-existent node returns 404
    missing_res = client.post("/api/nodes/non_existent_node/explain")
    assert missing_res.status_code == 404
