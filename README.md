<div align="center">

# ⌘ RepoLens

**Turn any codebase into a local, interactive architecture map in seconds.**

*Static-analysis-first. Zero runtime execution. Zero cloud leakage.*

[![CI](https://github.com/ompatelz/RepoLenz/actions/workflows/ci.yml/badge.svg)](https://github.com/ompatelz/RepoLenz/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-3776ab.svg?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![TypeScript / React 19](https://img.shields.io/badge/frontend-React%2019%20%7C%20React%20Flow-61dafb.svg?style=flat&logo=react&logoColor=black)](https://react.dev/)
[![License MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Safety](https://img.shields.io/badge/security-zero%20target%20execution-brightgreen.svg)](#non-negotiable-safety-guarantees)
[![Local First](https://img.shields.io/badge/privacy-100%25%20local--first-blueviolet.svg)](#quick-start)

</div>

---

## The Problem

Codebases grow into tangled webs of dependencies. Architecture diagrams in Confluence or Notion become obsolete the instant a pull request merges. Developers onboarding to new teams spend weeks tracing imports by hand, and PR reviewers routinely miss introduced architectural cycles or broken boundary layers.

## The RepoLens Solution

**RepoLens** inspects untrusted repositories statically—without importing code, running scripts, or installing dependencies—and turns the entire codebase into a living, interactive architecture graph:

```
[ Codebase (Python / JS / TS / React) ]
                   │
                   ▼ (Pure AST & Masked Lexical Parsing - Zero Execution)
       [ Unified Architecture Graph ]
                   │
    ┌──────────────┼──────────────┬──────────────┬──────────────┐
    ▼              ▼              ▼              ▼              ▼
[ Interactive  [ Boundary     [ Multi-Format [ CI Regression [ Bounded AI
  Web Map ]      Linter ]       Exporters ]    Diff Engine ]   Insights ]
```

---

## ✨ Key Features

| Feature | Description |
| :--- | :--- |
| **🌐 Interactive Web Map** | Built on React 19 & React Flow. Features semantic zoom, package breadcrumbs, 1-hop / 2-hop neighborhood focus, search, node filtering, and full ARIA keyboard shortcuts (`/`, `Ctrl+K`, `Esc`). |
| **⚡ Framework Intelligence** | Automatically detects FastAPI routes, HTTP methods, route handlers, and SQLAlchemy / SQLModel table entities and relationships. |
| **🧩 Polyglot Parsing** | Statically analyzes Python ASTs alongside JavaScript, TypeScript, JSX, and TSX files. Extracts imports, classes, functions, and React components with zero native binaries. |
| **🛡️ Architecture Linter** | `repolens check` enforces layer boundaries (e.g. `domain` cannot import `api`), flags circular dependencies, and caps fan-out thresholds in CI. |
| **📊 Multi-Format Exporters** | `repolens export` generates clean Mermaid (`.mmd`), PlantUML (`.puml`), Graphviz (`.dot`), or self-contained offline interactive HTML reports. |
| **🔄 Architecture Diff Engine** | `repolens diff` compares two repository commits or saved graphs to catch introduced dependency cycles or removed public API routes in CI. |
| **🤖 Bounded Architecture AI** | `repolens explain` provides structural insights using an offline rule synthesizer by default, or an optional OpenAI-compatible provider. Never uploads entire codebases. |

---

## ⚡ Quick Start

### 1. Installation

Install directly from checkout or wheel:

```bash
# Clone and install in development mode
git clone https://github.com/ompatelz/RepoLenz.git
cd RepoLenz
python -m pip install -e ".[dev]"
```

### 2. Instant Explorer

Launch the local interactive visualizer on your current project with a single command:

```bash
repolens .
```

*RepoLens spins up a local read-only loopback server (`http://127.0.0.1:7777`) and opens the packaged interactive explorer.*

---

## 💻 CLI Workflows

### Architecture Linter & CI Boundary Gating
Enforce layer purity and catch circular dependencies automatically in GitHub Actions:

```bash
# Verify architectural invariants with strict CI gating
repolens check ./my-project --strict

# Check against a custom rules configuration
repolens check ./my-project --rules .repolens/rules.json --json
```

*Example output:*
```text
Architecture Check: my-project
============================================================
Status:     FAILED
Violations: 2 (1 errors, 1 warnings)

[ERROR] layer-boundary: Core must not depend on API presentation layer: 'core.service' imports forbidden target 'api.routes' (core/service.py:12)
[WARNING] max-fan-out: Node 'app.main' exceeds maximum allowed fan-out (14 > 10)
```

### Export to Diagrams & Offline HTML Reports
Generate production-ready diagrams for pull requests or documentation:

```bash
# Export to Mermaid diagram syntax
repolens export ./my-project --format mermaid --output architecture.mmd

# Export to PlantUML component diagram
repolens export ./my-project --format plantuml --output architecture.puml

# Export a self-contained offline HTML report (ideal for CI artifacts & sharing)
repolens export ./my-project --format html --output architecture-report.html
```

### Architecture Graph Diff & Regression Prevention
Block pull requests that introduce dependency cycles or break public API contracts:

```bash
# Compare base branch vs current PR branch
repolens diff ./main-branch ./pr-branch --fail-on-regressions
```

*Example output:*
```text
Architecture Diff: main-branch -> pr-branch
============================================================
Summary: Architecture Diff: +3/-1 nodes, +5/-2 edges. New cycles: 1, Removed routes: 1.

Added Nodes (3):
  + [module] payment_gateway (module:payment_gateway)
  + [route] POST /api/v2/checkout (route:checkout_v2)

Removed Nodes (1):
  - [route] POST /api/v1/checkout (route:checkout_v1)

⚠️  New Dependency Cycles (1):
  • module:billing -> module:payment_gateway -> module:billing

⚠️  Removed Public Routes (1):
  • POST /api/v1/checkout
```

### Bounded Node Explanation
Get architectural impact and recommendations for any module, route, or model:

```bash
repolens explain ./my-project --node module:core.database
```

---

## 🔒 Non-Negotiable Safety Guarantees

RepoLens is purpose-built to analyze untrusted, private, and enterprise codebases safely:

- **Zero Target Code Execution:** Target code is never imported, invoked, or evaluated. No `setup.py` scripts or test runners are executed.
- **Zero Cloud Leakage by Default:** Core analysis, caching, graph generation, and rule verification run 100% locally.
- **Zero Mandatory API Keys:** Core features and offline architectural insights require no OpenAI or third-party cloud credentials.
- **Strictly Bounded Privacy:** When optional AI explanation is enabled, only 1-hop neighbor metadata and a tight 60-line excerpt are passed—never your full repository.
- **Loopback Only:** Local server binds strictly to `127.0.0.1`.

---

## 🛠️ Tech Stack & Engineering Highlights

- **Backend:** Python 3.12+, FastAPI, NetworkX, Pydantic V2, Typer, Uvicorn, Pathspec.
- **Frontend:** React 19, TypeScript, `@xyflow/react` (React Flow), Vite.
- **Test Suite:** Pytest (93 tests), Vitest (15 tests), isolated fresh-virtualenv wheel smoke tests in CI.
- **Code Quality:** Ruff format & lint check, Mypy strict mode across all modules.

---

## 📚 Documentation

- [CLI & Usage Guide](docs/usage.md)
- [Architecture & Analysis Model](docs/architecture.md)
- [Static Analysis Guarantees](docs/analysis.md)
- [Development & Contributing Guide](docs/development.md)
- [Benchmarking Methodology](docs/benchmarks.md)
- [Release Notes](docs/release-notes.md)
- [Milestone Engineering Notes](docs/progress/)

---

## 📄 License

RepoLens is open source software licensed under the [MIT License](LICENSE).
