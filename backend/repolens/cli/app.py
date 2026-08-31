"""The canonical RepoLens command-line entry point."""

from __future__ import annotations

import typer

from repolens import __version__

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
