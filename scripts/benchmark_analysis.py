"""Benchmark RepoLens scanning, AST parsing, and graph operations on synthetic repositories."""

from __future__ import annotations

import argparse
import tempfile
import time
from pathlib import Path

from repolens.analysis import analyze_repository
from repolens.graph import GraphEngine
from repolens.scanner import RepositoryScanner
from scripts.generate_synthetic_repo import generate_synthetic_repo


def run_benchmarks(num_packages: int = 10, modules_per_package: int = 10) -> None:
    """Execute timed micro-benchmarks on an isolated synthetic repository."""
    with tempfile.TemporaryDirectory(prefix=".repolens-perf-") as tmp_dir:
        repo_path = Path(tmp_dir)

        # 1. Generation
        meta = generate_synthetic_repo(
            repo_path, num_packages=num_packages, modules_per_package=modules_per_package
        )

        # 2. Scanning
        t0 = time.perf_counter()
        scanner = RepositoryScanner()
        scan_result = scanner.scan(repo_path)
        scan_time = time.perf_counter() - t0

        # 3. Static AST Analysis & Graph Document Construction
        t0 = time.perf_counter()
        doc = analyze_repository(repo_path)
        analysis_time = time.perf_counter() - t0

        # 4. Graph Engine Initialization & Statistics
        t0 = time.perf_counter()
        engine = GraphEngine(doc)
        _ = engine.stats()
        stats_time = time.perf_counter() - t0

        # 5. Cycle Detection
        t0 = time.perf_counter()
        cycles = engine.cycles()
        cycles_time = time.perf_counter() - t0

        # 6. Level Filtering (Modules)
        t0 = time.perf_counter()
        module_doc = engine.filter_level("module")
        level_filter_time = time.perf_counter() - t0

        # 7. Subgraph Extraction (2-hop)
        t0 = time.perf_counter()
        sample_node_id = doc.nodes[len(doc.nodes) // 2].id
        subgraph_doc = engine.subgraph(sample_node_id, depth=2)
        subgraph_time = time.perf_counter() - t0

    print("=" * 60)
    print(" REPOLENS STATIC ANALYSIS PERFORMANCE BENCHMARK")
    print("=" * 60)
    print(f"Synthetic codebase : {meta['packages']} packages, {meta['modules']} modules")
    print(f"Graph nodes        : {len(doc.nodes)} nodes, {len(doc.edges)} edges")
    print(f"Detected cycles    : {len(cycles)}")
    print("-" * 60)
    print(f"Repository scan    : {scan_time * 1000:7.2f} ms ({scan_result.file_count} files)")
    print(
        f"AST analysis & doc : {analysis_time * 1000:7.2f} ms "
        f"({meta['modules'] / analysis_time:5.1f} modules/sec)"
    )
    print(f"Graph stats        : {stats_time * 1000:7.2f} ms")
    print(f"Cycle detection    : {cycles_time * 1000:7.2f} ms")
    print(
        f"Level filter (mod) : {level_filter_time * 1000:7.2f} ms ({len(module_doc.nodes)} nodes)"
    )
    print(f"Subgraph (2-hop)   : {subgraph_time * 1000:7.2f} ms ({len(subgraph_doc.nodes)} nodes)")
    print("-" * 60)
    total_pipeline = (scan_time + analysis_time + stats_time + cycles_time) * 1000
    print(f"Total pipeline     : {total_pipeline:7.2f} ms")
    print("=" * 60)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packages", type=int, default=10, help="Number of packages.")
    parser.add_argument("--modules-per-package", type=int, default=10, help="Modules per package.")
    args = parser.parse_args()
    run_benchmarks(num_packages=args.packages, modules_per_package=args.modules_per_package)


if __name__ == "__main__":
    main()
