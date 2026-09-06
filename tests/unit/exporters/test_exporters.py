from repolens.exporters import (
    DotExporter,
    HtmlReportExporter,
    MermaidExporter,
    PlantUmlExporter,
    get_exporter,
)
from repolens.graph.engine import GraphEngine
from repolens.models.graph import Edge, EdgeType, GraphDocument, Node, NodeType


def sample_graph() -> GraphEngine:
    doc = GraphDocument(
        nodes=[
            Node(id="module:app", type=NodeType.MODULE, name="app"),
            Node(id="route:index", type=NodeType.ROUTE, name="GET /api/v1/items"),
            Node(id="model:user", type=NodeType.MODEL, name="User"),
            Node(id="component:ui", type=NodeType.COMPONENT, name="ItemList"),
        ],
        edges=[
            Edge(source="module:app", target="route:index", type=EdgeType.EXPOSES),
            Edge(source="module:app", target="model:user", type=EdgeType.USES),
            Edge(source="component:ui", target="route:index", type=EdgeType.CALLS),
        ],
        metadata={"repository": "demo"},
    )
    return GraphEngine(doc)


def test_mermaid_exporter() -> None:
    graph = sample_graph()
    output = MermaidExporter().export(graph)
    assert output.startswith("flowchart TD")
    assert "module_app" in output
    assert "route_index" in output
    assert "classDef route" in output
    assert "-->|exposes|" in output


def test_plantuml_exporter() -> None:
    graph = sample_graph()
    output = PlantUmlExporter().export(graph)
    assert "@startuml" in output
    assert "@enduml" in output
    assert 'boundary "GET /api/v1/items" as route_index' in output
    assert 'database "User" as model_user' in output


def test_dot_exporter() -> None:
    graph = sample_graph()
    output = DotExporter().export(graph)
    assert "digraph Architecture" in output
    assert "module_app" in output
    assert "shape=" in output


def test_html_exporter() -> None:
    graph = sample_graph()
    output = HtmlReportExporter().export(graph)
    assert "<!DOCTYPE html>" in output
    assert "RepoLens Architecture Snapshot: demo" in output
    assert "repolens-data" in output


def test_get_exporter_factory() -> None:
    assert isinstance(get_exporter("mermaid"), MermaidExporter)
    assert isinstance(get_exporter("plantuml"), PlantUmlExporter)
    assert isinstance(get_exporter("dot"), DotExporter)
    assert isinstance(get_exporter("html"), HtmlReportExporter)
