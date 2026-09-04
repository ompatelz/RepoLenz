from pathlib import Path

from repolens.analysis import analyze_repository


def test_builds_module_and_symbol_graph_from_fixture() -> None:
    root = Path(__file__).parents[1] / "fixtures" / "scanner" / "simple_python_project"
    graph = analyze_repository(root, use_cache=False)
    assert any(node.id == "module:main" for node in graph.nodes)
    assert any(node.name == "greeting" for node in graph.nodes)


def test_pipeline_can_skip_cache_for_ephemeral_analysis() -> None:
    root = Path(__file__).parents[1] / "fixtures" / "scanner" / "simple_python_project"

    assert analyze_repository(root, use_cache=False).nodes
