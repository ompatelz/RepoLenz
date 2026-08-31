# Foundation milestone

## Goal

Establish a small, installable Python foundation for RepoLens with reliable local
quality checks and continuous integration from the first contribution.

## Delivered

- A `src`-like backend package layout rooted at `backend/repolens`.
- A Typer CLI entry point with help and version commands.
- Extensible, typed graph node and edge domain models.
- Unit-test and fixture directories for future repository-analysis coverage.
- Packaging, linting, formatting, type-checking, testing, and build configuration.
- Open-source repository essentials: README, MIT license, and repository hygiene rules.

## Architecture decisions

- Use Python 3.12+ and Hatchling for a lightweight, standards-based package build.
- Keep product code in `backend/repolens` so a future frontend can remain a sibling
  application without mixing Python and Node tooling.
- Model graph primitives independently from parsers and graph algorithms to keep
  future language parsers and visualizations interoperable.
- Treat analyzed repositories as untrusted input; future analysis must parse source
  files without importing or executing them.

## Tests

- CLI tests verify the public help and version surface.
- Model tests verify graph-node and graph-edge validation.
- A minimal Python fixture repository establishes the fixture convention.

## CI changes

GitHub Actions runs Python 3.12 checks for pushes and pull requests:

- dependency installation
- Ruff formatting and linting
- strict mypy checks
- pytest
- source and wheel build validation

## Known limitations

- The CLI foundation does not yet scan or analyze a repository.
- No web application or API is included yet.
- Python analysis and architecture insights are future milestones.

## Next milestone

Build a structured repository scanner that detects files, packages, manifests,
entry points, and common ignored paths without executing target code.
