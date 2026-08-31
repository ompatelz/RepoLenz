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
