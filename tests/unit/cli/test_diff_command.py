import json
from pathlib import Path

from typer.testing import CliRunner

from repolens.cli.app import app


def test_diff_command_same_fixture() -> None:
    fixture = Path(__file__).parents[2] / "fixtures" / "scanner" / "simple_python_project"
    runner = CliRunner()
    result = runner.invoke(app, ["diff", str(fixture), str(fixture)])
    assert result.exit_code == 0
    assert "Architecture Diff:" in result.output
    assert "+0/-0 nodes" in result.output


def test_diff_command_json_output() -> None:
    fixture = Path(__file__).parents[2] / "fixtures" / "scanner" / "simple_python_project"
    runner = CliRunner()
    result = runner.invoke(app, ["diff", str(fixture), str(fixture), "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["has_breaking_changes"] is False
    assert len(data["added_nodes"]) == 0
