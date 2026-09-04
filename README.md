# RepoLens

**Turn a Python codebase into a local, interactive architecture map.**

RepoLens is a static-analysis-first tool for understanding unfamiliar Python
repositories. It reads source and project metadata to build an architecture graph;
it does **not** import, execute, or modify the repository being analyzed.

> **Status:** early, local-first software. The current release is suitable for
> exploring Python repositories and validating the analysis pipeline. Its output is
> evidence from static source inspection, not a substitute for runtime tracing.

## What it does today

- Safely scans repository structure while respecting the root `.gitignore` and
  excluding common generated directories.
- Parses Python with the standard-library `ast` module to extract modules, imports,
  classes, functions, methods, inheritance, decorators, signatures, docstrings, and
  syntax errors.
- Detects static evidence for FastAPI routes and dependencies plus SQLAlchemy and
  SQLModel models.
- Builds a directed architecture graph with containment and resolvable-import
  relationships, graph statistics, dependency paths, neighborhoods, and cycle
  detection.
- Serves a local, read-only API and bundled browser shell for examining one analysis
  graph.

## Requirements

- Python 3.12 or newer

No API key, cloud account, or network connection is required to analyze a target
repository after RepoLens is installed.

## Install

From a checkout:

```bash
python -m pip install -e ".[dev]"
```

Or install a built wheel:

```bash
python -m build
python -m pip install dist/repolens-*.whl
```

## Quick start

```bash
# Inspect a repository without running it.
repolens scan ./my-project

# Build and save its complete architecture graph.
repolens graph ./my-project --output architecture.json

# Open the local browser experience at http://127.0.0.1:7777.
repolens serve ./my-project
```

The server binds to `127.0.0.1` by default and exposes a read-only local API. See
the [usage guide](docs/usage.md) for every command and endpoint.

## Safety and scope

RepoLens treats the analyzed repository as untrusted input. It traverses and reads
files only; it does not execute Python, run package managers, start target services,
or upload source code. It avoids symlink traversal and ignores common VCS, virtual
environment, dependency, cache, and build-output directories.

Static analysis has natural limits. Dynamic imports, runtime-generated routes,
metaprogramming, and framework conventions outside the current detectors may be
unresolved or absent. Read [analysis guarantees and limitations](docs/analysis.md)
before using output for high-confidence architectural decisions.

## Development

```bash
python -m pip install -e ".[dev]"
ruff format --check .
ruff check .
mypy backend/repolens
pytest
python -m build
python scripts/smoke_wheel_install.py \
  --wheel dist/repolens-*.whl \
  --fixture tests/fixtures/scanner/simple_python_project
```

The frontend is developed separately:

```bash
cd frontend
npm ci
npm run build
```

Contributor expectations, CI checks, and release verification are in the
[development guide](docs/development.md). Benchmarks are opt-in and documented in
the [benchmark guide](docs/benchmarks.md); the project deliberately does not publish
unreproducible performance claims.

## Documentation

- [Usage guide](docs/usage.md)
- [Architecture and analysis model](docs/architecture.md)
- [Safety guarantees and limitations](docs/analysis.md)
- [Development and release guide](docs/development.md)
- [Benchmark methodology](docs/benchmarks.md)
- [Release notes](docs/release-notes.md)
- Historical [milestone notes](docs/progress/)

## Contributing

Keep changes focused, include tests where behavior changes, and ensure the local
quality checks pass before opening a pull request. Please build on a named feature
branch and merge through a reviewed PR into `main`.

## License

RepoLens is released under the [MIT License](LICENSE).
