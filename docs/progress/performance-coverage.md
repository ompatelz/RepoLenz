# Performance Coverage and Scalability Benchmarks

## Overview

RepoLens is built to scale across medium-to-large repositories without lagging or exhausting
memory. Feature 7 establishes synthetic repository generation, automated performance testing,
and benchmark profiling.

## Benchmark Methodology

Using `scripts/generate_synthetic_repo.py`, synthetic codebases are generated on-demand with:
- Configurable package and module counts (e.g. 10 packages, 110 modules, 800+ nodes).
- Realistic cross-package imports, service classes, methods, and functions.
- FastAPI routes (`@router.get`) and SQLAlchemy ORM models (`class Model(Base)`).
- Controlled dependency cycles to exercise Tarjan/Johnson cycle detection algorithms.

## Baseline Performance Profile

Measured on a standard multi-package application with **110 modules** and **813 graph nodes**:

| Pipeline Stage | Timing | Throughput / Scope |
| --- | --- | --- |
| **Repository Scanner** | ~9 ms | 112 files cataloged |
| **AST Analysis & Document** | ~150 ms | **>700 modules / second** |
| **Graph Statistics** | ~8 ms | Full node & relationship counting |
| **Cycle Detection** | ~3 ms | Complete cycle enumeration |
| **Level Filtering (`module`)** | ~1.3 ms | Dynamic graph projection |
| **Subgraph Extraction (`depth=2`)**| ~0.6 ms | Bounded BFS neighborhood |
| **Total End-to-End Pipeline** | **< 180 ms** | Complete repository analysis |

## Automated Test Coverage

- `tests/perf/test_large_repository_benchmark.py` runs in continuous integration, ensuring
  that no code changes introduce regressions to scan, parse, cycle detection, or subgraph
  extraction speeds.
- CLI profiling tool available via `python scripts/benchmark_analysis.py --packages N --modules-per-package M`.
