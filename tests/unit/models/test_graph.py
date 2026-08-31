from repolens.models import Edge, EdgeType, GraphDocument, Node, NodeType


def test_graph_document_serializes_stable_contract() -> None:
    node = Node(id="module:app.main", type=NodeType.MODULE, name="main", path="app/main.py")
    edge = Edge(source="repository:demo", target=node.id, type=EdgeType.CONTAINS)

    document = GraphDocument(nodes=[node], edges=[edge])

    assert document.model_dump(mode="json") == {
        "schema_version": "1",
        "metadata": {},
        "nodes": [
            {
                "id": "module:app.main",
                "type": "module",
                "name": "main",
                "path": "app/main.py",
                "line_start": None,
                "line_end": None,
                "metadata": {},
            }
        ],
        "edges": [
            {
                "source": "repository:demo",
                "target": "module:app.main",
                "type": "contains",
                "metadata": {},
            }
        ],
        "stats": {},
        "insights": {},
    }
