# Analysis guarantees and limitations

## Guarantees

- RepoLens does not import, execute, or modify the target repository.
- Python source is parsed with the standard-library `ast` module.
- The scanner does not traverse symlinks and excludes common generated, dependency,
  cache, and version-control directories.
- The scanner applies `.gitignore` rules from the target repository root.
- The local server binds to loopback (`127.0.0.1`) and exposes read-only endpoints.

## Important limitations

- Python, JavaScript, JSX, TypeScript, and TSX files are statically analyzed.
  Other source types are inventoried but not semantically parsed.
- Cross-language relationships are never fabricated without static evidence; Python
  and JavaScript import spaces resolve within their respective module ecosystems.
- Only the root `.gitignore` is evaluated. Nested ignore files and global Git
  exclusions are not currently applied.
- Import resolution is conservative. Dynamic imports, import hooks, namespace
  package edge cases, and runtime path changes can leave relationships unresolved.
- Framework detection is heuristic static evidence, not execution tracing. FastAPI
  route decorators, APIRouter inclusion, `Depends` injection, and SQLAlchemy/SQLModel
  models are extracted strictly from AST patterns without executing target code.
- Entry points are conventional filename heuristics rather than proof of runtime
  behavior.
- A successfully parsed file is not proof that it would execute successfully; a
  file with a syntax error is reported independently of other files.

Treat the graph as a fast map for investigation. Validate critical architectural,
security, or production-runtime conclusions against tests, configuration, and the
running system.
