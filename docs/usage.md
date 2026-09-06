# Usage guide

RepoLens commands take a local repository directory. Paths can be relative or
absolute. The target is analyzed statically and is never executed.

## Scan a repository

```bash
repolens scan ./my-project
repolens scan ./my-project --json
```

`scan` inventories files, Python packages, source roots, tests, project manifests,
configuration, likely entry points, and root `.gitignore` rules. `--json` emits a
machine-readable scan document.

## Inspect Python syntax

```bash
repolens analyze ./my-project
repolens analyze ./my-project --json
```

`analyze` parses discovered Python files with `ast`. It reports source-derived
modules, imports, symbols, inheritance, decorators, signatures, docstrings, and
isolated syntax errors. A syntax error in one file is reported without stopping
analysis of the remaining files.

## Create an architecture graph

```bash
repolens graph ./my-project
repolens graph ./my-project --output architecture.json
repolens stats ./my-project
repolens cycles ./my-project
```

`graph` emits the normalized graph as JSON. `--output` writes it to a file instead
of standard output. `stats` provides a concise count summary, while `cycles` lists
detected directed dependency cycles or reports that none were found.

## Explore in the browser

```bash
repolens ./my-project
repolens .
repolens serve ./my-project --port 8787
```

Open the address printed by the command (by default,
`http://127.0.0.1:7777`). The server is intentionally local-only and read-only. It
hosts the bundled browser assets when they are present in the installation.

The API is available at:

| Endpoint | Description |
| --- | --- |
| `GET /api/graph` | Full architecture graph document; accepts `?level=repository\|module\|symbol\|all`. |
| `GET /api/stats` | Graph counts, cycle summary, route counts, and model counts. |
| `GET /api/insights` | Derived graph insights. |
| `GET /api/nodes/{node_id}` | One graph node. |
| `GET /api/nodes/{node_id}/neighbors?direction=both` | Neighboring nodes; use `in`, `out`, or `both`. |
| `GET /api/nodes/{node_id}/subgraph?depth=1` | N-hop neighborhood subgraph bounded by depth (1–5). |

## Exit behavior

An invalid or non-directory repository path produces a clear CLI error and exits
with status code `2`. Use `repolens --help` for the installed command reference and
`repolens --version` to identify the installed version.
