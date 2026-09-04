from repolens.graph import GraphEngine
from repolens.models import Edge, EdgeType, GraphDocument, Node, NodeType


def build_document() -> GraphDocument:
    repository = Node(id="repository:demo", type=NodeType.REPOSITORY, name="demo")
    api = Node(id="module:demo.api", type=NodeType.MODULE, name="api")
    service = Node(id="module:demo.service", type=NodeType.MODULE, name="service")
    database = Node(id="module:demo.database", type=NodeType.MODULE, name="database")
    return GraphDocument(
        nodes=[repository, api, service, database],
        edges=[
            Edge(source=repository.id, target=api.id, type=EdgeType.CONTAINS),
            Edge(source=api.id, target=service.id, type=EdgeType.IMPORTS),
            Edge(source=service.id, target=database.id, type=EdgeType.IMPORTS),
            Edge(source=database.id, target=api.id, type=EdgeType.IMPORTS),
            Edge(source=api.id, target=service.id, type=EdgeType.USES),
        ],
    )


def test_node_returns_graph_node_or_none() -> None:
    engine = GraphEngine(build_document())

    assert engine.node("module:demo.api") == Node(
        id="module:demo.api", type=NodeType.MODULE, name="api"
    )
    assert engine.node("module:missing") is None


def test_neighbors_respects_direction_and_deduplicates_parallel_relationships() -> None:
    engine = GraphEngine(build_document())

    assert [node.id for node in engine.neighbors("module:demo.api", "outgoing")] == [
        "module:demo.service"
    ]
    assert [node.id for node in engine.neighbors("module:demo.api", "incoming")] == [
        "module:demo.database",
        "repository:demo",
    ]
    assert [node.id for node in engine.neighbors("module:demo.api")] == [
        "module:demo.database",
        "module:demo.service",
        "repository:demo",
    ]


def test_subgraph_limits_hops_and_keeps_internal_edges() -> None:
    engine = GraphEngine(build_document())

    one_hop = engine.subgraph("module:demo.api")
    two_hops = engine.subgraph("module:demo.api", depth=2)

    assert [node.id for node in one_hop.nodes] == [
        "module:demo.api",
        "module:demo.database",
        "module:demo.service",
        "repository:demo",
    ]
    assert len(one_hop.edges) == 5
    assert {node.id for node in two_hops.nodes} == {
        "repository:demo",
        "module:demo.api",
        "module:demo.service",
        "module:demo.database",
    }


def test_shortest_path_uses_directed_relationships() -> None:
    engine = GraphEngine(build_document())

    assert [
        node.id for node in engine.shortest_path("repository:demo", "module:demo.database")
    ] == [
        "repository:demo",
        "module:demo.api",
        "module:demo.service",
        "module:demo.database",
    ]


def test_cycles_and_stats_report_directed_cycle() -> None:
    engine = GraphEngine(build_document())

    assert engine.cycles() == [["module:demo.api", "module:demo.database", "module:demo.service"]]
    assert engine.stats() == {"nodes": 4, "edges": 5, "cycles": 1}


def test_insights_rank_evidence_backed_dependencies() -> None:
    insights = GraphEngine(build_document()).insights()

    assert insights["cycles"] == [
        ["module:demo.api", "module:demo.database", "module:demo.service"]
    ]
    assert insights["dependency_hubs"] == ["module:demo.api", "module:demo.service"]
    assert insights["fan_out"] == ["module:demo.api"]
    assert insights["orphans"] == []


def test_serialize_returns_original_graph_contract() -> None:
    document = build_document()

    assert GraphEngine(document).serialize() is document
