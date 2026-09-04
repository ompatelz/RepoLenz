"""Measure static scan and analysis duration for one local repository."""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from repolens.analysis import analyze_repository
from repolens.scanner import RepositoryScanner


def _measure(operation: Callable[[], object], runs: int, warmup: int) -> list[float]:
    """Run an operation with excluded warm-up iterations and return milliseconds."""
    for _ in range(warmup):
        operation()
    samples: list[float] = []
    for _ in range(runs):
        started = time.perf_counter()
        operation()
        samples.append((time.perf_counter() - started) * 1_000)
    return samples


def _summary(samples: list[float]) -> dict[str, float]:
    """Return stable summary values for non-empty timing samples."""
    return {
        "median_ms": round(statistics.median(samples), 3),
        "min_ms": round(min(samples), 3),
        "max_ms": round(max(samples), 3),
    }


def main() -> None:
    """Benchmark scan and analysis operations without executing target code."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="Repository directory to measure.")
    parser.add_argument("--runs", type=int, default=10, help="Measured iterations (default: 10).")
    parser.add_argument(
        "--warmup", type=int, default=2, help="Excluded warm-up iterations (default: 2)."
    )
    arguments = parser.parse_args()
    path = arguments.path.resolve()
    if not path.is_dir():
        parser.error(f"path is not a directory: {path}")
    if arguments.runs < 1:
        parser.error("--runs must be at least 1")
    if arguments.warmup < 0:
        parser.error("--warmup cannot be negative")

    scanner = RepositoryScanner()
    scan_result = scanner.scan(path)
    scan_samples = _measure(lambda: scanner.scan(path), arguments.runs, arguments.warmup)
    analysis_samples = _measure(lambda: analyze_repository(path), arguments.runs, arguments.warmup)
    result: dict[str, Any] = {
        "repository": str(path),
        "runs": arguments.runs,
        "warmup": arguments.warmup,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "files": scan_result.file_count,
        "python_files": len(scan_result.python_files),
        "scan": _summary(scan_samples),
        "analysis": _summary(analysis_samples),
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
