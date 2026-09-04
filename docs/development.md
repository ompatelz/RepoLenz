# Development and release guide

## Local setup

```bash
python -m pip install -e ".[dev]"
cd frontend && npm ci
```

Run Python commands from the repository root. Run frontend commands from
`frontend/`.

## Quality gate

Before opening a pull request, run:

```bash
ruff format --check .
ruff check .
mypy backend/repolens
pytest
python -m build
python scripts/smoke_wheel_install.py \
  --wheel dist/repolens-*.whl \
  --fixture tests/fixtures/scanner/simple_python_project
cd frontend && npm run build
```

The wheel smoke test creates an isolated virtual environment, installs the built
wheel, verifies the installed `repolens` command, scans the fixture, and writes a
graph. It guards against editable-install-only behavior and missing console scripts.

GitHub Actions runs formatting, linting, strict typing, tests, package build, wheel
installation smoke coverage, and the frontend production build on pull requests and
pushes to `main`.

## Contribution workflow

1. Branch from current `main` using a focused name such as `feat/graph-search` or
   `fix/import-resolution`.
2. Keep each PR centered on one user-visible capability or coherent repair.
3. Add tests for behavior and update public documentation when commands, APIs, or
   guarantees change.
4. Use conventional, descriptive commits (for example,
   `feat: add module search` or `fix: resolve relative package imports`).
5. Open a PR into `main`; merge only after required checks pass.

## Release checklist

Use this checklist before publishing a tagged release:

- Confirm the version in `pyproject.toml` and `backend/repolens/_version.py` match.
- Run the full quality gate from a clean checkout.
- Verify a wheel install in an isolated environment with the smoke script.
- Verify `repolens --version`, `repolens --help`, `scan`, `graph`, and `serve` on a
  representative local repository.
- Confirm the package includes browser assets when shipping the browser experience.
- Add a dated entry to [release notes](release-notes.md) with user-visible changes,
  compatibility notes, and known limitations.
- Create the Git tag and GitHub release from the verified commit.

RepoLens does not currently publish packages automatically. Keep release creation
manual until the publishing identity, package index, and provenance requirements are
explicitly configured.
