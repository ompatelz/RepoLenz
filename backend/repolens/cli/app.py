"""The canonical RepoLens command-line entry point."""

from __future__ import annotations

import typer

from repolens import __version__
from repolens.scanner import RepositoryScan, RepositoryScanner

app = typer.Typer(
    name="repolens",
    help="Turn a codebase into an interactive architecture map.",
    no_args_is_help=True,
)


def version_callback(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show the installed RepoLens version and exit.",
    ),
) -> None:
    """Explore codebase architecture without executing target code."""


@app.command()
def scan(
    path: str = typer.Argument(..., help="Repository directory to inspect."),
    json_output: bool = typer.Option(
        False, "--json", help="Emit the structured scan result as JSON."
    ),
) -> None:
    """Inventory a repository without importing or executing its code."""
    try:
        result = RepositoryScanner().scan(path)
    except (FileNotFoundError, NotADirectoryError) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(code=2) from error

    if json_output:
        typer.echo(result.model_dump_json(indent=2))
        return
    _render_scan(result)


def _render_scan(result: RepositoryScan) -> None:
    typer.echo(f"Repository: {result.name}")
    typer.echo()
    typer.echo(f"Files                {result.file_count}")
    typer.echo(f"Python files         {len(result.python_files)}")
    typer.echo(f"Directories          {result.directory_count}")
    typer.echo(f"Python packages      {len(result.packages)}")
    typer.echo(f"Tests                {len(result.tests)}")
    if result.dependency_manifests:
        typer.echo("\nDependency manifests")
        for manifest in result.dependency_manifests:
            typer.echo(f"• {manifest}")
    if result.entrypoints:
        typer.echo("\nPossible entry points")
        for entrypoint in result.entrypoints:
            typer.echo(f"• {entrypoint}")
