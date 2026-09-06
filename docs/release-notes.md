# Release notes

## Unreleased

### Added

- Safe repository scanning and Python AST analysis through the `repolens` CLI.
- Framework-aware static evidence for FastAPI, SQLAlchemy, and SQLModel.
- End-to-end integration of framework route, model, and dependency nodes into the architecture graph.
- Directed architecture graph generation, graph statistics, and cycle reporting.
- Semantic zoom, hierarchical breadcrumb drill-down, and neighborhood focus navigation in the web explorer.
- Keyboard shortcuts (`/`, `Ctrl+K`, `Escape`) and ARIA accessibility standards throughout the browser UI.
- Direct root CLI execution (`repolens .` / `repolens <path>`) defaulting to the local browser experience.
- Reproducible web packaging tooling (`scripts/sync_web_assets.py`) and CI drift verification.
- Synthetic repository benchmarking suite and automated performance regression tests.
- JavaScript and TypeScript static analysis parser supporting ES6/CommonJS imports, classes, functions, methods, and React components.
- Polyglot repository analysis mapping Python and JavaScript/TypeScript codebases with truthful module boundaries.
- Local read-only HTTP API and bundled browser experience via `repolens serve`.
- Isolated wheel-install smoke coverage in continuous integration.

### Safety and compatibility

- RepoLens requires Python 3.12 or newer.
- RepoLens analyzes repositories statically and does not execute target code in any language.
- Python, JavaScript, JSX, TypeScript, and TSX files are parsed with zero external binary or runtime requirements.

### Known limitations

- Analysis and import resolution are intentionally conservative.
- The browser experience is local-first and the server binds to loopback only.
- Packaging and release publishing remain manual until a package distribution target
  is configured.
