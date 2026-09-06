# CLI Default Root Command

## Overview

RepoLens is designed to offer the fastest path from terminal to codebase architecture map.
Previously, launching the web explorer required typing `repolens serve <path>`. With Feature 4,
`repolens <path>` (such as `repolens .`) directly launches the local server experience while
fully preserving explicit subcommands (`scan`, `analyze`, `graph`, `stats`, `cycles`, `serve`).

## Implementation Details

1. **Custom `DefaultRootGroup` (TyperGroup subclass)**:
   - Extends Typer's Click group to check CLI arguments upon parsing.
   - If the first argument is not a registered subcommand and does not match top-level help
     or version flags (`--help`, `-h`, `--version`), the command automatically prepends
     `serve`, seamlessly routing the path and optional flags (e.g. `--port`) to the server.

2. **Graceful Path Validation**:
   - `serve` cleanly captures `(FileNotFoundError, NotADirectoryError)` and reports a formatted
     error message to standard error with exit code `2`, consistent with all other RepoLens subcommands.

3. **Subcommand & Flag Preservation**:
   - Explicit commands like `repolens scan .`, `repolens graph .`, and `repolens stats .` execute normally.
   - Top-level `--help` and `--version` continue to report root product metadata and version strings.
   - Local options like `--port` can be passed either after the path (`repolens . --port 8000`) or before.

4. **Automated & Wheel Smoke Verification**:
   - Unit tests in `tests/unit/cli/test_app.py` verify direct invocation, port configuration, and error reporting.
   - Wheel installation smoke test in `scripts/smoke_wheel_install.py` validates the console script in a clean isolated virtual environment.
