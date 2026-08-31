# RepoLens

**Turn any codebase into an interactive architecture map.**

RepoLens is a local, static-analysis-first developer tool for understanding Python
repositories. It is designed to inspect source code without importing or executing
the repository being analyzed.

## Current capabilities

RepoLens can safely inventory a repository's files, Python packages, manifests,
configuration files, tests, source directories, and likely entry points. It also
provides typed domain contracts that later analysis and visualization layers share.

## Requirements

- Python 3.12 or newer

## Installation

For local development:

```bash
python -m pip install -e ".[dev]"
```

## Usage

```bash
repolens --help
repolens --version
repolens scan ./my-project
repolens scan ./my-project --json
repolens analyze ./my-project
repolens analyze ./my-project --json
```

The primary product command will ultimately be:

```bash
repolens ./my-project
```

## Design principles

- **Static analysis first:** useful with no API keys, LLMs, or external AI services.
- **Python-first:** Python's built-in `ast` will provide the initial parser.
- **CLI-first:** the CLI is the canonical entry point; the web UI will explore its results.
- **Safe by design:** target repositories are untrusted input and are never executed as part of analysis.

## Development

```bash
ruff format --check .
ruff check .
mypy backend/repolens
pytest
python -m build
```

Continuous integration runs these checks on Python 3.12 for every pull request and
push to the default development branches.

## Roadmap

Python analysis extracts imports, classes, functions, methods, decorators,
inheritance, signatures, docstrings, and source ranges with the built-in AST.
The next milestones add framework-aware detection, a directed architecture graph,
and an interactive local application.
Progress notes live in [`docs/progress`](docs/progress/).

## Contributing

Contributions are welcome as the project takes shape. Please keep changes focused,
add or update tests, and ensure the local quality checks pass before opening a pull
request.

## License

RepoLens is released under the [MIT License](LICENSE).
