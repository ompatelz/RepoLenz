from __future__ import annotations

import json
from pathlib import Path

import pytest

from repolens.cache import AnalysisCache
from repolens.models import GraphDocument, Node, NodeType


def _graph() -> GraphDocument:
    return GraphDocument(
        metadata={"repository": "demo"},
        nodes=[Node(id="repository:demo", type=NodeType.REPOSITORY, name="demo")],
    )


def test_returns_graph_when_source_fingerprint_matches(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("answer = 42\n", encoding="utf-8")
    cache = AnalysisCache()
    cache.store(tmp_path, _graph())

    assert cache.load(tmp_path) == _graph()


def test_invalidates_when_source_content_changes_even_with_same_size(tmp_path: Path) -> None:
    source = tmp_path / "app.py"
    source.write_text("answer = 42\n", encoding="utf-8")
    cache = AnalysisCache()
    cache.store(tmp_path, _graph())
    source.write_text("answer = 24\n", encoding="utf-8")

    assert cache.load(tmp_path) is None


def test_invalidates_when_source_file_is_added_or_removed(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("answer = 42\n", encoding="utf-8")
    cache = AnalysisCache()
    cache.store(tmp_path, _graph())
    (tmp_path / "added.py").write_text("answer = 24\n", encoding="utf-8")

    assert cache.load(tmp_path) is None

    cache.store(tmp_path, _graph())
    (tmp_path / "added.py").unlink()
    assert cache.load(tmp_path) is None


def test_ignores_cache_and_non_source_files_when_fingerprinting(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("answer = 42\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("first\n", encoding="utf-8")
    cache = AnalysisCache()
    cache.store(tmp_path, _graph())
    (tmp_path / "README.md").write_text("second\n", encoding="utf-8")

    assert cache.load(tmp_path) == _graph()


def test_corrupt_payload_is_treated_as_cache_miss(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("answer = 42\n", encoding="utf-8")
    payload = tmp_path / ".repolens" / "graph.json"
    payload.parent.mkdir()
    payload.write_text("not valid json", encoding="utf-8")

    assert AnalysisCache().load(tmp_path) is None


def test_get_or_create_reports_cache_hit_and_writes_json_payload(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("answer = 42\n", encoding="utf-8")
    cache = AnalysisCache()
    calls = 0

    def build() -> GraphDocument:
        nonlocal calls
        calls += 1
        return _graph()

    graph, from_cache = cache.get_or_create(tmp_path, build)
    cached_graph, cached = cache.get_or_create(tmp_path, build)

    assert (graph, from_cache) == (_graph(), False)
    assert (cached_graph, cached) == (_graph(), True)
    assert calls == 1
    payload = json.loads((tmp_path / ".repolens" / "graph.json").read_text(encoding="utf-8"))
    assert payload["version"] == 1
    assert payload["fingerprint"]["files"][0]["path"] == "app.py"


def test_get_or_create_returns_analysis_when_cache_write_is_not_permitted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cache = AnalysisCache()

    def reject_cache_write(repository: Path | str, graph: GraphDocument) -> None:
        raise PermissionError("read-only repository")

    monkeypatch.setattr(cache, "store", reject_cache_write)

    assert cache.get_or_create(tmp_path, _graph) == (_graph(), False)


def test_explicit_invalidation_removes_only_the_cache_payload(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("answer = 42\n", encoding="utf-8")
    cache = AnalysisCache()
    cache.store(tmp_path, _graph())

    assert cache.invalidate(tmp_path) is True
    assert cache.invalidate(tmp_path) is False
    assert (tmp_path / ".repolens").is_dir()
    assert not (tmp_path / ".repolens" / "graph.json").exists()


def test_rejects_invalid_source_suffixes() -> None:
    with pytest.raises(ValueError, match="Source suffixes"):
        AnalysisCache(("py",))
