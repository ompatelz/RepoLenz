from pathlib import Path

from repolens.analysis import analyze_repository
from repolens.models import EdgeType, NodeType

POLYGLOT_FIXTURE = Path(__file__).parents[1] / "fixtures" / "scanner" / "mixed_polyglot_project"


def test_polyglot_analysis_constructs_unified_graph() -> None:
    graph = analyze_repository(POLYGLOT_FIXTURE, use_cache=False)

    assert graph.metadata["repository"] == "mixed_polyglot_project"
    assert int(graph.stats["modules"]) >= 6
    assert int(graph.stats["components"]) >= 3

    # Verify component nodes
    components = {n.name: n for n in graph.nodes if n.type == NodeType.COMPONENT}
    assert "App" in components
    assert "Header" in components
    assert "ItemList" in components

    # Verify python backend routes
    routes = {n.name: n for n in graph.nodes if n.type == NodeType.ROUTE}
    assert any("GET /api/items" in r for r in routes)

    # Verify internal module imports in frontend
    import_edges = [(e.source, e.target) for e in graph.edges if e.type == EdgeType.IMPORTS]
    assert ("module:frontend.src.App", "module:frontend.src.components.Header") in import_edges
    assert ("module:frontend.src.App", "module:frontend.src.components.ItemList") in import_edges
    assert (
        "module:frontend.src.components.ItemList",
        "module:frontend.src.utils.format",
    ) in import_edges

    # Verify NO cross-language imports are fabricated
    for src, tgt in import_edges:
        if "backend" in src:
            assert "frontend" not in tgt
        if "frontend" in src:
            assert "backend" not in tgt
