# Scalable Subgraph APIs Progress

## Goal
Provide scalable, bounded graph query capabilities on both the graph engine and local HTTP API to support large repositories without transferring thousands of unnecessary symbol nodes to browser clients.

## Implemented
- Added `GraphEngine.filter_level(level)` to filter nodes and edges by architectural hierarchy (`repository`, `module`, `symbol`, `all`), while updating subgraph-specific node, edge, and cycle stats.
- Added level filtering to `GET /api/graph` via the `?level=repository|module|symbol|all` query parameter, validating levels with informative 400 errors.
- Added `GET /api/nodes/{node_id}/subgraph` with bounded traversal depth (`depth: int = Query(default=1, ge=1, le=5)`).
- Validated depth bounds (1–5) and node existence, returning 404 for nonexistent nodes and 422 for invalid depths.
- Retained full graph endpoint compatibility when `level` parameter is omitted.
- Ensured stable `GraphDocument` contract across all new and filtered endpoints.

## Architecture Decisions
- **Stable Schema**: All endpoints return `GraphDocument`, avoiding separate schemas for full graphs vs. subgraphs.
- **Strict Bounds**: Depth is bounded between 1 and 5 hops in FastAPI query validation to prevent denial-of-service or performance degradation on dense graphs.
- **Level Stratification**: `level=repository` contains repository and package nodes; `level=module` contains repository, package, and module nodes (and module-level edges); `level=symbol` returns the complete graph.

## Tests
- Added `test_filter_level_filters_hierarchy_and_updates_stats` in `tests/unit/graph/test_engine.py`.
- Added `test_filter_level_rejects_invalid_levels` in `tests/unit/graph/test_engine.py`.
- Added `test_subgraph_validates_bounds_and_node_existence` in `tests/unit/graph/test_engine.py`.
- Added `test_graph_endpoint_supports_level_filter` in `tests/unit/api/test_analysis_api.py`.
- Added `test_node_subgraph_endpoint_returns_bounded_neighborhood` in `tests/unit/api/test_analysis_api.py`.
- Verified all 45 unit tests pass cleanly.

## CI Changes
- No workflow changes required; fully tested through existing test suite.

## Known Limitations
- Filtering currently operates on pre-computed repository graphs; streaming or lazy parsing of unbounded monoliths is deferred to large-repository optimizations.

## Next Work
- Implement semantic zoom and multi-level graph navigation in the web explorer (Package collapse/expand, focus mode, breadcrumbs, hop neighborhoods).
