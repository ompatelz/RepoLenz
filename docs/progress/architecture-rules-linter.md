# Architecture Rules & Invariant Linter Progress

## Goal

Provide automated architectural boundary and invariant verification (layer protection, circular dependency enforcement, fan-out caps) via `repolens check` and `GET /api/rules/check`, allowing developers and CI pipelines to prevent architectural drift without runtime execution.

## Implemented

- **Architecture Rules Engine (`backend/repolens/rules/`):**
  - `LayerBoundaryRule`: Pattern matching on source and forbidden target module/package names or paths.
  - `ArchitectureRuleEngine`: Statically detects layer violations, dependency cycles, and excessive fan-out.
  - `load_rules`: Automatically discovers `.repolens/rules.json` or `architecture_rules.json` or loads custom rule files.
- **CLI Command (`backend/repolens/cli/app.py`):**
  - `repolens check <path> [--rules <file>] [--strict] [--json]`.
  - Exits with non-zero status code on errors or warnings (in `--strict` mode) for seamless CI gating.
- **API Endpoint (`backend/repolens/api/app.py`):**
  - `GET /api/rules/check` returning structured `RuleCheckReport`.

## Tests & Verification

- `tests/unit/rules/test_rule_engine.py`: Unit tests for clean graphs, layer boundary violations, cycle detection, and fan-out limits.
- `tests/unit/cli/test_check_command.py`: CLI testing for human-readable output, JSON mode, and exit codes.
