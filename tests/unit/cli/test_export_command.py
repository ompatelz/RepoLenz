from pathlib import Path

from typer.testing import CliRunner

from repolens.cli.app import app


def test_export_command_stdout() -> None:
    fixture = Path(__file__).parents[2] / "fixtures" / "scanner" / "simple_python_project"
    runner = CliRunner()
    result = runner.invoke(app, ["export", str(fixture), "--format", "mermaid"])
    assert result.exit_code == 0
    assert "flowchart TD" in result.output


def test_export_command_file_output(tmp_path: Path) -> None:
    fixture = Path(__file__).parents[2] / "fixtures" / "scanner" / "simple_python_project"
    out_file = tmp_path / "architecture.puml"
    runner = CliRunner()
    result = runner.invoke(
        app, ["export", str(fixture), "--format", "plantuml", "--output", str(out_file)]
    )
    assert result.exit_code == 0
    assert out_file.is_file()
    assert "@startuml" in out_file.read_text(encoding="utf-8")


def test_export_command_html_report(tmp_path: Path) -> None:
    fixture = Path(__file__).parents[2] / "fixtures" / "scanner" / "simple_python_project"
    out_html = tmp_path / "report.html"
    runner = CliRunner()
    result = runner.invoke(
        app, ["export", str(fixture), "--format", "html", "--output", str(out_html)]
    )
    assert result.exit_code == 0
    assert "<!DOCTYPE html>" in out_html.read_text(encoding="utf-8")
