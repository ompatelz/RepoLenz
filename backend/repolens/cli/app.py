"""The canonical RepoLens command-line entry point."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from repolens import __version__
from repolens.analysis import analyze_repository
from repolens.graph import GraphEngine
from repolens.parsers import PythonAstParser
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


@app.command()
def analyze(
    path: str = typer.Argument(..., help="Repository directory to statically analyze."),
    json_output: bool = typer.Option(False, "--json", help="Emit normalized analysis as JSON."),
) -> None:
    """Analyze Python syntax without importing or executing target code."""
    try:
        scan_result = RepositoryScanner().scan(path)
    except (FileNotFoundError, NotADirectoryError) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(code=2) from error

    parser = PythonAstParser()
    analyses = [
        parser.parse_file(
            Path(scan_result.root) / item,
            item.removesuffix(".py").replace("/", "."),
        )
        for item in scan_result.python_files
    ]
    if json_output:
        typer.echo(json.dumps([item.model_dump(mode="json") for item in analyses], indent=2))
        return
    symbols = [symbol for item in analyses for symbol in item.symbols]
    imports = [item for analysis in analyses for item in analysis.imports]
    typer.echo(f"Analyzed {len(analyses)} Python files\n")
    typer.echo(f"Modules        {len(analyses)}")
    typer.echo(f"Classes        {sum(item.kind.value == 'class' for item in symbols)}")
    typer.echo(f"Functions      {sum(item.kind.value == 'function' for item in symbols)}")
    typer.echo(f"Methods        {sum(item.kind.value == 'method' for item in symbols)}")
    typer.echo(f"Imports        {len(imports)}")
    typer.echo(f"Unresolved     {sum(item.kind.value == 'unresolved' for item in imports)}")


@app.command()
def graph(
    path: str = typer.Argument(..., help="Repository directory to map."),
    output: Path | None = typer.Option(None, "--output", help="Write graph JSON to this path."),
) -> None:
    """Build an architecture graph without executing target code."""
    try:
        document = analyze_repository(path)
    except (FileNotFoundError, NotADirectoryError) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(code=2) from error
    payload = document.model_dump_json(indent=2)
    if output:
        output.write_text(payload, encoding="utf-8")
        typer.echo(f"Wrote graph to {output}")
        return
    typer.echo(payload)


@app.command()
def stats(path: str = typer.Argument(..., help="Repository directory to inspect.")) -> None:
    """Print architecture graph statistics."""
    values = GraphEngine(analyze_repository(path)).stats()
    for name, value in values.items():
        typer.echo(f"{name.title():<10} {value}")


@app.command()
def cycles(path: str = typer.Argument(..., help="Repository directory to inspect.")) -> None:
    """Print detected dependency cycles."""
    found = GraphEngine(analyze_repository(path)).cycles()
    if not found:
        typer.echo("No dependency cycles detected.")
        return
    for cycle in found:
        typer.echo(" -> ".join(cycle))
