"""Verify a built wheel installs and exposes the RepoLens CLI in isolation."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
import venv
from pathlib import Path


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    """Run one checked command and retain text output for validation."""
    return subprocess.run(args, check=True, capture_output=True, text=True)


def _console_script(environment: Path) -> Path:
    """Return the platform-specific console-script path in a virtual environment."""
    scripts = environment / ("Scripts" if os.name == "nt" else "bin")
    return scripts / ("repolens.exe" if os.name == "nt" else "repolens")


def main() -> None:
    """Install one wheel into a fresh environment and exercise essential commands."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel", required=True, type=Path, help="Built wheel to install.")
    parser.add_argument(
        "--fixture",
        required=True,
        type=Path,
        help="Repository fixture to analyze with the installed CLI.",
    )
    arguments = parser.parse_args()
    wheel = arguments.wheel.resolve()
    fixture = arguments.fixture.resolve()
    if not wheel.is_file():
        parser.error(f"wheel does not exist: {wheel}")
    if not fixture.is_dir():
        parser.error(f"fixture is not a directory: {fixture}")

    with tempfile.TemporaryDirectory(prefix="repolens-wheel-smoke-") as temporary_directory:
        environment = Path(temporary_directory) / "venv"
        venv.EnvBuilder(with_pip=True, clear=True).create(environment)
        python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        _run(str(python), "-m", "pip", "install", "--disable-pip-version-check", str(wheel))

        command = _console_script(environment)
        version = _run(str(command), "--version").stdout.strip()
        scan = json.loads(_run(str(command), "scan", str(fixture), "--json").stdout)
        graph_path = Path(temporary_directory) / "architecture.json"
        _run(str(command), "graph", str(fixture), "--output", str(graph_path))
        graph = json.loads(graph_path.read_text(encoding="utf-8"))

    if not version:
        raise RuntimeError("installed CLI did not print a version")
    if scan.get("root") != str(fixture):
        raise RuntimeError("installed CLI scanned an unexpected fixture path")
    if "nodes" not in graph or "edges" not in graph:
        raise RuntimeError("installed CLI did not produce a graph document")
    print(f"wheel smoke passed: version={version}, nodes={len(graph['nodes'])}")


if __name__ == "__main__":
    main()
