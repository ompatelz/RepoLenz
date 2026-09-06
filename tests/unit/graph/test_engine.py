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

    assert engine.stats() == {
        "nodes": 4,
        "edges": 5,
        "cycles": 1,
        "routes": 0,
        "models": 0,
    }


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


def test_filter_level_filters_hierarchy_and_updates_stats() -> None:
    repository = Node(id="repository:demo", type=NodeType.REPOSITORY, name="demo")
    module = Node(id="module:demo.main", type=NodeType.MODULE, name="main")
    symbol = Node(id="symbol:demo.main:run", type=NodeType.FUNCTION, name="run")
    document = GraphDocument(
        nodes=[repository, module, symbol],
        edges=[
            Edge(source=repository.id, target=module.id, type=EdgeType.CONTAINS),
            Edge(source=module.id, target=symbol.id, type=EdgeType.CONTAINS),
        ],
    )
    engine = GraphEngine(document)

    repo_graph = engine.filter_level("repository")
    assert [n.id for n in repo_graph.nodes] == [repository.id]
    assert repo_graph.stats["nodes"] == 1
    assert repo_graph.stats["edges"] == 0

    module_graph = engine.filter_level("module")
    assert {n.id for n in module_graph.nodes} == {repository.id, module.id}
    assert module_graph.stats["nodes"] == 2
    assert module_graph.stats["edges"] == 1

    symbol_graph = engine.filter_level("symbol")
    assert len(symbol_graph.nodes) == 3


def test_filter_level_rejects_invalid_levels() -> None:
    import pytest

    engine = GraphEngine(build_document())
    with pytest.raises(ValueError, match="Invalid level"):
        engine.filter_level("invalid_level")


def test_subgraph_validates_bounds_and_node_existence() -> None:
    import pytest

    engine = GraphEngine(build_document())
    with pytest.raises(ValueError, match="depth must be at least 1"):
        engine.subgraph("module:demo.api", depth=0)

    with pytest.raises(KeyError, match="Node not found"):
        engine.subgraph("module:nonexistent", depth=1)
