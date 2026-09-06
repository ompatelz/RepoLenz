import json
from pathlib import Path

from typer.testing import CliRunner

from repolens.cli.app import app


def test_explain_command_text_output() -> None:
    fixture = Path(__file__).parents[2] / "fixtures" / "scanner" / "simple_python_project"
    runner = CliRunner()
    result = runner.invoke(
        app, ["explain", str(fixture), "--node", "module:main", "--provider", "offline"]
    )
    assert result.exit_code == 0
    assert "Architecture Explanation: module:main" in result.output
    assert "Role:" in result.output
    assert "Summary:" in result.output


def test_explain_command_json_output() -> None:
    fixture = Path(__file__).parents[2] / "fixtures" / "scanner" / "simple_python_project"
    runner = CliRunner()
    result = runner.invoke(
        app, ["explain", str(fixture), "--node", "module:main", "--provider", "mock", "--json"]
    )
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["node_id"] == "module:main"

    assert payload["provider"] == "mock"
    assert "summary" in payload


def test_explain_command_missing_node() -> None:
    fixture = Path(__file__).parents[2] / "fixtures" / "scanner" / "simple_python_project"
    runner = CliRunner()
    result = runner.invoke(app, ["explain", str(fixture), "--node", "non_existent_node"])
    assert result.exit_code == 1
    assert "not found" in result.output
