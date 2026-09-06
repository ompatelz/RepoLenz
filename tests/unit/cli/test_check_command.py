import json
from pathlib import Path

from typer.testing import CliRunner

from repolens.cli.app import app


def test_check_command_clean_repo() -> None:
    fixture = Path(__file__).parents[2] / "fixtures" / "scanner" / "simple_python_project"
    runner = CliRunner()
    result = runner.invoke(app, ["check", str(fixture)])
    assert result.exit_code == 0
    assert "PASSED" in result.output
    assert "All architectural invariants and boundary checks passed." in result.output


def test_check_command_json_output() -> None:
    fixture = Path(__file__).parents[2] / "fixtures" / "scanner" / "simple_python_project"
    runner = CliRunner()
    result = runner.invoke(app, ["check", str(fixture), "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["passed"] is True
    assert data["violations_count"] == 0


def test_check_command_custom_failing_rules(tmp_path: Path) -> None:
    fixture = Path(__file__).parents[2] / "fixtures" / "scanner" / "simple_python_project"
    rules_file = tmp_path / "strict_rules.json"
    rules_file.write_text(
        json.dumps(
            {
                "allow_cycles": False,
                "layer_boundaries": [
                    {
                        "source_pattern": "main",
                        "forbidden_target_pattern": "simple_package*",
                        "description": "Main must not import simple_package",
                        "severity": "error",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(app, ["check", str(fixture), "--rules", str(rules_file)])
    assert result.exit_code == 1
    assert "FAILED" in result.output
    assert "layer-boundary" in result.output
