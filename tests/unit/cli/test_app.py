from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from repolens.cli.app import app

runner = CliRunner()


def test_help_describes_product() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "interactive architecture map" in result.output


def test_version_is_available() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert result.output.strip() == "0.1.0"


def test_default_command_serves_repository() -> None:
    fixture = Path(__file__).parents[2] / "fixtures" / "scanner" / "simple_python_project"
    with patch("uvicorn.run") as mock_run:
        result = runner.invoke(app, [str(fixture)])
        assert result.exit_code == 0
        assert "RepoLens API running at http://127.0.0.1:7777" in result.output
        mock_run.assert_called_once()
        _, kwargs = mock_run.call_args
        assert kwargs["port"] == 7777


def test_default_command_accepts_port_flag() -> None:
    fixture = Path(__file__).parents[2] / "fixtures" / "scanner" / "simple_python_project"
    with patch("uvicorn.run") as mock_run:
        result = runner.invoke(app, [str(fixture), "--port", "9999"])
        assert result.exit_code == 0
        assert "RepoLens API running at http://127.0.0.1:9999" in result.output
        mock_run.assert_called_once()
        _, kwargs = mock_run.call_args
        assert kwargs["port"] == 9999


def test_default_command_fails_gracefully_on_missing_path() -> None:
    result = runner.invoke(app, ["./non_existent_path_404"])
    assert result.exit_code == 2
    assert "Error:" in result.output


def test_explicit_serve_command_still_works() -> None:
    fixture = Path(__file__).parents[2] / "fixtures" / "scanner" / "simple_python_project"
    with patch("uvicorn.run") as mock_run:
        result = runner.invoke(app, ["serve", str(fixture), "--port", "8888"])
        assert result.exit_code == 0
        assert "RepoLens API running at http://127.0.0.1:8888" in result.output
        mock_run.assert_called_once()
        _, kwargs = mock_run.call_args
        assert kwargs["port"] == 8888
