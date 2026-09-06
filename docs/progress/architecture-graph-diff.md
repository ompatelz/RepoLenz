# Architecture Graph Diff Progress

## Goal

Provide automated architecture evolution tracking, regression prevention, and diffing between two codebases or saved architecture graphs via `repolens diff` and `POST /api/diff`.

## Implemented

- **Diff Engine Subsystem (`backend/repolens/diff/`):**
  - `compute_graph_diff`: Identifies added/removed nodes, added/removed relationships, newly introduced cycles, and dropped public API routes.
  - `GraphDiffReport`: Encapsulates high-level summary, change lists, and boolean `has_breaking_changes` indicator.
- **CLI Command (`backend/repolens/cli/app.py`):**
  - `repolens diff <base_path> <target_path> [--fail-on-regressions] [--json]`.
  - Seamlessly parses either directory paths or `.json` architecture graph documents.
- **API Endpoint (`backend/repolens/api/app.py`):**
  - `POST /api/diff`: Compares an uploaded `GraphDocument` against the currently loaded server graph.

## Tests & Verification

- `tests/unit/diff/test_diff_engine.py`: Unit tests for additions, deletions, breaking route changes, and cycle regressions.
- `tests/unit/cli/test_diff_command.py`: CLI testing for human-readable output and JSON mode.
