from pathlib import Path

from typer.testing import CliRunner

from repolens.cli.app import app


def test_graph_and_stats_commands_build_fixture_graph(tmp_path: Path) -> None:
    fixture = Path(__file__).parents[2] / "fixtures" / "scanner" / "simple_python_project"
    output = tmp_path / "graph.json"
    runner = CliRunner()
    assert runner.invoke(app, ["graph", str(fixture), "--output", str(output)]).exit_code == 0
    assert '"nodes"' in output.read_text(encoding="utf-8")
    assert "Nodes" in runner.invoke(app, ["stats", str(fixture)]).output
