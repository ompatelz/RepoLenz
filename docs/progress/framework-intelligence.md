# Framework Intelligence Progress

## Goal
Integrate static framework detection into the end-to-end RepoLens static analysis pipeline, promoting FastAPI routes, dependency injection, and SQLAlchemy/SQLModel models into first-class graph elements with evidence-backed relationships, accurate stats, and interactive visualization.

## Implemented
- Integrated `FrameworkDetector` into `backend/repolens/analysis.py`.
- Emitted first-class `route` nodes with HTTP method, path, handler, tags, and response model metadata.
- Emitted first-class `model` nodes for SQLAlchemy and SQLModel database models with table names, field lists, and base class metadata.
- Created `CALLS` edges from routes to their respective handler functions.
- Created `DEPENDS_ON` edges from handler functions to dependency providers evidenced via `Depends(...)`, statically resolving internal dependencies or generating `dependency` nodes.
- Created `INHERITS` edges between model subclasses and their base models.
- Created `USES` edges for `include_router` connections between modules.
- Updated `GraphEngine.stats()` and `GraphDocument.stats` to count `routes` and `models`.
- Updated web frontend navigation and canvas legend to display Route and Model metrics and indicators.
- Added a realistic FastAPI and SQLAlchemy fixture project with false-positive test cases.

## Architecture Decisions
- **Static Evidence Only**: No target source code is imported or executed. All framework constructs are detected purely through Python AST matching.
- **Model Node Promotion**: Classes identified as database models are assigned `type=NodeType.MODEL` and prefixed with `model:`, enabling distinct filtering and visualization while retaining containment of their internal methods.
- **Dependency Resolution**: `Depends(...)` references are resolved against local module symbols and imports first; unresolved/external dependencies create `NodeType.DEPENDENCY` nodes without inventing phantom symbols.
- **Subclass Recognition**: Model detection iteratively tracks models defined or imported across modules so derived models inherit model classification and form `INHERITS` graph edges.

## Tests
- Added `test_builds_framework_aware_graph_with_routes_models_and_dependencies` in `tests/unit/test_analysis_pipeline.py`.
- Added `test_framework_detection_avoids_false_positives` in `tests/unit/test_analysis_pipeline.py`.
- Updated unit test assertions in `tests/unit/graph/test_engine.py` and `tests/unit/api/test_analysis_api.py`.
- Verified CLI output with `repolens stats` on the new fixture.
- Passed full pytest suite, ruff format, ruff lint, and mypy type checks.

## CI Changes
- No workflow YAML modifications were required; all additions conform to existing CI jobs (Python quality/tests, wheel smoke test, and frontend build).

## Known Limitations
- Router path prefixes specified dynamically or via multiple nesting levels without static strings are not concatenated into full URLs.
- Cross-language API route mappings (e.g. frontend fetch calls to backend routes) are out of scope for V1 Python analysis.

## Next Work
- Implement scalable subgraph APIs (`/api/graph?level=...` and `/api/nodes/{id}/subgraph?depth=...`) for large repositories.
