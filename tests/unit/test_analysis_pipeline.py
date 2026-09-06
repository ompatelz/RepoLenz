from pathlib import Path

from repolens.analysis import analyze_repository
from repolens.models import EdgeType, NodeType


def test_builds_module_and_symbol_graph_from_fixture() -> None:
    root = Path(__file__).parents[1] / "fixtures" / "scanner" / "simple_python_project"
    graph = analyze_repository(root, use_cache=False)
    assert any(node.id == "module:main" for node in graph.nodes)
    assert any(node.name == "greeting" for node in graph.nodes)


def test_pipeline_can_skip_cache_for_ephemeral_analysis() -> None:
    root = Path(__file__).parents[1] / "fixtures" / "scanner" / "simple_python_project"

    assert analyze_repository(root, use_cache=False).nodes


def test_builds_framework_aware_graph_with_routes_models_and_dependencies() -> None:
    root = Path(__file__).parents[1] / "fixtures" / "frameworks" / "fastapi_orm_project"
    graph = analyze_repository(root, use_cache=False)

    # Verify counts in graph stats
    assert graph.stats["routes"] == 3
    assert graph.stats["models"] == 3

    # Verify route nodes
    routes = {node.id: node for node in graph.nodes if node.type == NodeType.ROUTE}
    assert "route:app.main:GET:/health" in routes
    health_route = routes["route:app.main:GET:/health"]
    assert health_route.name == "GET /health"
    assert health_route.metadata["tags"] == ["system"]
    assert health_route.line_start is not None and health_route.line_start > 0

    assert "route:app.api.routes:GET:/" in routes
    assert "route:app.api.routes:POST:/" in routes

    # Verify route-to-handler CALLS edges
    route_call_edges = [
        (edge.source, edge.target) for edge in graph.edges if edge.type == EdgeType.CALLS
    ]
    assert ("route:app.main:GET:/health", "symbol:app.main:health_check") in route_call_edges
    assert ("route:app.api.routes:GET:/", "symbol:app.api.routes:list_users") in route_call_edges
    assert ("route:app.api.routes:POST:/", "symbol:app.api.routes:create_user") in route_call_edges

    # Verify model nodes and metadata
    models = {node.id: node for node in graph.nodes if node.type == NodeType.MODEL}
    assert "model:app.models.user:User" in models
    user_model = models["model:app.models.user:User"]
    assert user_model.name == "User"
    assert user_model.metadata["table_name"] == "users"
    assert "id" in user_model.metadata["fields"]
    assert "username" in user_model.metadata["fields"]
    assert "posts" in user_model.metadata["fields"]

    assert "model:app.models.user:AdminUser" in models
    assert "model:app.models.post:Post" in models
    post_model = models["model:app.models.post:Post"]
    assert post_model.metadata["table_name"] == "posts"

    # Verify model inheritance edge
    inherits_edges = [
        (edge.source, edge.target) for edge in graph.edges if edge.type == EdgeType.INHERITS
    ]
    assert ("model:app.models.user:AdminUser", "model:app.models.user:User") in inherits_edges

    # Verify handler-to-dependency DEPENDS_ON edges
    depends_edges = [
        (edge.source, edge.target) for edge in graph.edges if edge.type == EdgeType.DEPENDS_ON
    ]
    assert (
        "symbol:app.api.routes:list_users",
        "symbol:app.dependencies:get_user_service",
    ) in depends_edges
    assert (
        "symbol:app.api.routes:create_user",
        "symbol:app.dependencies:get_user_service",
    ) in depends_edges

    # Verify router inclusion USES edge
    uses_edges = [(edge.source, edge.target) for edge in graph.edges if edge.type == EdgeType.USES]
    assert ("module:app.main", "module:app.api.routes") in uses_edges


def test_framework_detection_avoids_false_positives() -> None:
    root = Path(__file__).parents[1] / "fixtures" / "frameworks" / "fastapi_orm_project"
    graph = analyze_repository(root, use_cache=False)

    nodes_by_id = {node.id: node for node in graph.nodes}

    # PlainHelper, NotAnOrmModel, and Base should be CLASS nodes, NOT MODEL nodes
    assert "symbol:app.utils.not_framework:PlainHelper" in nodes_by_id
    assert nodes_by_id["symbol:app.utils.not_framework:PlainHelper"].type == NodeType.CLASS

    assert "symbol:app.utils.not_framework:NotAnOrmModel" in nodes_by_id
    assert nodes_by_id["symbol:app.utils.not_framework:NotAnOrmModel"].type == NodeType.CLASS

    assert "symbol:app.models.base:Base" in nodes_by_id
    assert nodes_by_id["symbol:app.models.base:Base"].type == NodeType.CLASS

    # Non-route methods and non-string decorators should not produce ROUTE nodes
    route_paths = [node.name for node in graph.nodes if node.type == NodeType.ROUTE]
    assert not any("decorated_with_int" in p for p in route_paths)
    assert not any("PlainHelper" in p for p in route_paths)

    # func_with_default should not produce DEPENDS_ON edges
    depends_sources = [edge.source for edge in graph.edges if edge.type == EdgeType.DEPENDS_ON]
    assert "symbol:app.utils.not_framework:func_with_default" not in depends_sources
