# Repository scanner milestone

## Goal

Provide a fast, structured, and safe repository inventory as the first input to
RepoLens analysis.

## Delivered

- `repolens scan <path>` for a concise terminal summary.
- `repolens scan <path> --json` for a stable structured result.
- Detection of files, directories, Python files, Python packages, tests, source
  directories, manifests, configuration files, README, `.gitignore`, and likely
  Python entry points.
- Deterministic repository-relative POSIX paths on every platform.
- Default exclusion of version control, virtual environments, build artifacts,
  dependency directories, cache directories, and symlink traversal.
- Root `.gitignore` support through git-compatible matching rules.

## Architecture decisions

- The scanner only reads directory entries and text from the target `.gitignore`;
  it never imports, executes, or evaluates target-repository code.
- Scanner results are a Pydantic model rather than terminal-specific state, so the
  upcoming parser, graph engine, and local API can consume the same data.
- A single package scanner owns traversal and filtering, keeping CLI rendering
  separate from filesystem analysis.

## Tests

- Simple and nested Python projects.
- Package markers, manifests, configuration files, tests, source roots, and entry
  points.
- `.gitignore` patterns and standard tool-generated exclusions.
- Empty repositories and native/Windows-style path strings.

## CI changes

The existing Python quality, type, test, and build checks now cover scanner code
and fixture repositories.

## Known limitations

- `.gitignore` is evaluated from the scanned root only; nested ignore files and
  global Git excludes are not yet applied.
- Entrypoints are conventional filename heuristics, not framework-aware evidence.

## Next milestone

Parse Python source with `ast` into normalized symbols, imports, inheritance, and
source-location data.
