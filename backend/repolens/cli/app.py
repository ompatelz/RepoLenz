"""The canonical RepoLens command-line entry point."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer
import uvicorn
from typer.core import TyperGroup

from repolens import __version__
from repolens.ai import build_node_context, get_provider
from repolens.analysis import analyze_repository
from repolens.api import create_app
from repolens.graph import GraphEngine
from repolens.parsers import PythonAstParser
from repolens.rules import ArchitectureRuleEngine, load_rules
from repolens.scanner import RepositoryScan, RepositoryScanner


class DefaultRootGroup(TyperGroup):
    """A TyperGroup that routes direct repository paths or serve options to the serve command."""

    default_command_name: str = "serve"

    def parse_args(self, ctx: Any, args: list[str]) -> list[str]:
        if not args and self.no_args_is_help:
            return super().parse_args(ctx, args)
        if args:
            first = args[0]
            if first not in self.commands and first not in ("--help", "-h", "--version"):
                args = [self.default_command_name] + list(args)
        return super().parse_args(ctx, args)


app = typer.Typer(
    cls=DefaultRootGroup,
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


@app.command()
def serve(
    path: str = typer.Argument(..., help="Repository directory to explore."),
    port: int = typer.Option(7777, "--port", help="Local HTTP port."),
) -> None:
    """Serve a local, read-only architecture API."""
    try:
        repo_path = Path(path)
        document = analyze_repository(repo_path)
    except (FileNotFoundError, NotADirectoryError) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(code=2) from error
    typer.echo(f"RepoLens API running at http://127.0.0.1:{port}")
    uvicorn.run(create_app(document, repo_root=repo_path), host="127.0.0.1", port=port)


@app.command()
def explain(
    path: str = typer.Argument(..., help="Repository directory containing the node."),
    node_id: str = typer.Option(
        ..., "--node", "-n", help="Node ID to explain (e.g. module or symbol)."
    ),
    provider: str = typer.Option(
        "offline", "--provider", "-p", help="Provider: 'offline', 'openai', or 'mock'."
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit explanation as JSON."),
) -> None:
    """Generate an architectural explanation for a graph node."""
    try:
        repo_path = Path(path)
        document = analyze_repository(repo_path)
    except (FileNotFoundError, NotADirectoryError) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(code=2) from error

    graph_engine = GraphEngine(document)
    if graph_engine.node(node_id) is None:
        typer.echo(f"Error: Node '{node_id}' not found in architecture graph.", err=True)
        raise typer.Exit(code=1)

    try:
        active_provider = get_provider(provider)
        context = build_node_context(graph_engine, node_id, repo_root=repo_path)
        explanation = active_provider.explain(context)
    except Exception as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(code=1) from error

    if json_output:
        typer.echo(explanation.model_dump_json(indent=2))
        return

    typer.echo(f"\nArchitecture Explanation: {explanation.node_id}")
    typer.echo("=" * 60)
    typer.echo(f"Role:                  {explanation.role}")
    typer.echo(f"Provider:              {explanation.provider}")
    typer.echo(f"\nSummary:\n  {explanation.summary}")
    typer.echo(f"\nArchitectural Impact:\n  {explanation.architectural_impact}")
    typer.echo(f"\nDependencies Context:\n  {explanation.dependencies_summary}")
    if explanation.recommendations:
        typer.echo("\nRecommendations:")
        for rec in explanation.recommendations:
            typer.echo(f"  • {rec}")
    typer.echo()


@app.command()
def check(
    path: str = typer.Argument(..., help="Repository directory to verify."),
    rules_file: Path | None = typer.Option(
        None, "--rules", "-r", help="Path to custom rules JSON file."
    ),
    strict: bool = typer.Option(False, "--strict", help="Fail on warnings as well as errors."),
    json_output: bool = typer.Option(False, "--json", help="Emit report as JSON."),
) -> None:
    """Verify architectural boundaries, invariants, and cycles."""
    try:
        repo_path = Path(path)
        document = analyze_repository(repo_path)
    except (FileNotFoundError, NotADirectoryError) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(code=2) from error

    config = load_rules(rules_path=rules_file, repo_root=repo_path)
    report = ArchitectureRuleEngine(config).check(GraphEngine(document))

    if json_output:
        typer.echo(report.model_dump_json(indent=2))
        if not report.passed or (strict and report.warning_count > 0):
            raise typer.Exit(code=1)
        return

    typer.echo(f"\nArchitecture Check: {repo_path.name}")
    typer.echo("=" * 60)
    typer.echo(f"Status:     {'PASSED' if report.passed else 'FAILED'}")
    typer.echo(
        f"Violations: {report.violations_count} "
        f"({report.error_count} errors, {report.warning_count} warnings)\n"
    )

    if not report.violations:
        typer.echo("✓ All architectural invariants and boundary checks passed.")
    else:
        for violation in report.violations:
            loc = (
                f" ({violation.path}:{violation.line})" if violation.path and violation.line else ""
            )
            typer.echo(
                f"[{violation.severity.upper()}] {violation.rule_id}: {violation.message}{loc}"
            )

    if not report.passed or (strict and report.warning_count > 0):
        raise typer.Exit(code=1)
