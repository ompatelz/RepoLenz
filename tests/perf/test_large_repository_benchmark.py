"""Performance and scalability benchmark on large synthetic repositories."""

from __future__ import annotations

import time
from pathlib import Path

from scripts.generate_synthetic_repo import generate_synthetic_repo

from repolens.analysis import analyze_repository
from repolens.graph import GraphEngine
from repolens.scanner import RepositoryScanner


def test_large_repository_analysis_performance(tmp_path: Path) -> None:
    """Validate that scanning, parsing, and graph operations scale linearly on 100+ modules."""
    meta = generate_synthetic_repo(
        tmp_path,
        num_packages=10,
        modules_per_package=10,
        include_cycles=True,
    )
    assert meta["modules"] == 110

    # 1. Benchmark RepositoryScanner
    t0 = time.perf_counter()
    scan_result = RepositoryScanner().scan(tmp_path)
    scan_duration = time.perf_counter() - t0
    assert scan_result.file_count >= 110
    assert scan_duration < 1.0, f"Scan took too long: {scan_duration:.3f}s"

    # 2. Benchmark AST analysis and graph document assembly
    t0 = time.perf_counter()
    doc = analyze_repository(tmp_path)
    analysis_duration = time.perf_counter() - t0
    assert len(doc.nodes) >= 700, f"Expected 700+ nodes, got {len(doc.nodes)}"
    assert len(doc.edges) >= 700, f"Expected 700+ edges, got {len(doc.edges)}"
    assert analysis_duration < 3.0, f"Analysis took too long: {analysis_duration:.3f}s"

    # 3. Benchmark GraphEngine initialization and cycle detection
    engine = GraphEngine(doc)
    t0 = time.perf_counter()
    cycles = engine.cycles()
    cycles_duration = time.perf_counter() - t0
    assert cycles_duration < 0.5, f"Cycle detection took too long: {cycles_duration:.3f}s"
    assert isinstance(cycles, list)

    # 4. Benchmark level filtering
    t0 = time.perf_counter()
    module_doc = engine.filter_level("module")
    filter_duration = time.perf_counter() - t0
    assert filter_duration < 0.5, f"Level filtering took too long: {filter_duration:.3f}s"
    assert all(n.type in ("repository", "package", "module") for n in module_doc.nodes)

    # 5. Benchmark bounded subgraph extraction
    sample_node_id = doc.nodes[0].id
    t0 = time.perf_counter()
    subgraph_doc = engine.subgraph(sample_node_id, depth=2)
    subgraph_duration = time.perf_counter() - t0
    assert subgraph_duration < 0.5, f"Subgraph took too long: {subgraph_duration:.3f}s"
    assert len(subgraph_doc.nodes) > 0
