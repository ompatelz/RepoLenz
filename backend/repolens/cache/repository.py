"""Safe on-disk caching for static repository analysis results.

The cache is deliberately scoped to a repository's ``.repolens`` directory.
Entries are accepted only when a fresh fingerprint of the repository's Python
source files matches the fingerprint stored with the graph document.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from repolens.models import GraphDocument

_CACHE_VERSION = 1
_CACHE_DIRECTORY = ".repolens"
_CACHE_FILENAME = "graph.json"
_DEFAULT_EXCLUDED_DIRECTORIES = frozenset(
    {
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".repolens",
        ".ruff_cache",
        ".venv",
        "__pycache__",
        "build",
        "coverage",
        "dist",
        "node_modules",
        "venv",
    }
)


class SourceFileFingerprint(BaseModel):
    """Content and stat metadata for one source file."""

    model_config = ConfigDict(frozen=True)

    path: str
    size: int = Field(ge=0)
    mtime_ns: int = Field(ge=0)
    content_sha256: str


class RepositoryFingerprint(BaseModel):
    """Deterministic identity of the source files used for an analysis."""

    model_config = ConfigDict(frozen=True)

    files: tuple[SourceFileFingerprint, ...]
    digest: str


class _CacheEnvelope(BaseModel):
    """Versioned cache payload, kept private to permit future migrations."""

    model_config = ConfigDict(frozen=True)

    version: int
    fingerprint: RepositoryFingerprint
    graph: GraphDocument


class AnalysisCache:
    """Read and write a graph cache that is invalidated by source changes.

    Only Python files are fingerprinted by default because the current analysis
    pipeline parses Python. Callers can opt into another source suffix set when
    they add parsers for additional languages.
    """

    def __init__(self, source_suffixes: Iterable[str] = (".py",)) -> None:
        suffixes = frozenset(source_suffixes)
        if not suffixes or any(not suffix.startswith(".") for suffix in suffixes):
            msg = "Source suffixes must be non-empty extensions such as '.py'."
            raise ValueError(msg)
        self._source_suffixes = suffixes

    def load(self, repository: Path | str) -> GraphDocument | None:
        """Return the cached graph when it exactly matches current source files."""

        root = self._root(repository)
        payload = self._read_payload(self._cache_path(root))
        if payload is None or payload.version != _CACHE_VERSION:
            return None
        if payload.fingerprint != self.fingerprint(root):
            return None
        return payload.graph

    def store(self, repository: Path | str, graph: GraphDocument) -> None:
        """Atomically store ``graph`` with a fingerprint of its source inputs."""

        root = self._root(repository)
        cache_path = self._cache_path(root)
        cache_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        envelope = _CacheEnvelope(
            version=_CACHE_VERSION,
            fingerprint=self.fingerprint(root),
            graph=graph,
        )
        self._atomic_write(cache_path, envelope.model_dump(mode="json"))

    def get_or_create(
        self,
        repository: Path | str,
        build: Callable[[], GraphDocument],
    ) -> tuple[GraphDocument, bool]:
        """Get a valid cached graph or build, persist, and return a fresh graph.

        The returned boolean is ``True`` only when the graph came from cache.
        """

        cached = self.load(repository)
        if cached is not None:
            return cached, True
        graph = build()
        try:
            self.store(repository, graph)
        except OSError:
            # Analysis remains useful for read-only repositories; caching is an
            # opportunistic optimization, never a prerequisite for a result.
            pass
        return graph, False

    def invalidate(self, repository: Path | str) -> bool:
        """Remove this repository's graph payload, returning whether it existed."""

        path = self._cache_path(self._root(repository))
        try:
            path.unlink()
        except FileNotFoundError:
            return False
        return True

    def fingerprint(self, repository: Path | str) -> RepositoryFingerprint:
        """Hash the selected source tree in a stable, path-independent order."""

        root = self._root(repository)
        files = tuple(self._fingerprint_file(root, path) for path in self._source_files(root))
        encoded = json.dumps(
            [item.model_dump(mode="json") for item in files],
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        return RepositoryFingerprint(files=files, digest=hashlib.sha256(encoded).hexdigest())

    def _source_files(self, root: Path) -> list[Path]:
        files: list[Path] = []
        for current, directory_names, file_names in os.walk(root, topdown=True, followlinks=False):
            current_path = Path(current)
            directory_names[:] = sorted(
                name
                for name in directory_names
                if name not in _DEFAULT_EXCLUDED_DIRECTORIES
                and not (current_path / name).is_symlink()
            )
            for file_name in sorted(file_names):
                path = current_path / file_name
                if (
                    path.suffix in self._source_suffixes
                    and path.is_file()
                    and not path.is_symlink()
                ):
                    files.append(path)
        return sorted(files, key=lambda path: path.relative_to(root).as_posix())

    @staticmethod
    def _fingerprint_file(root: Path, path: Path) -> SourceFileFingerprint:
        stat = path.stat()
        content_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        return SourceFileFingerprint(
            path=path.relative_to(root).as_posix(),
            size=stat.st_size,
            mtime_ns=stat.st_mtime_ns,
            content_sha256=content_hash,
        )

    @staticmethod
    def _root(repository: Path | str) -> Path:
        root = Path(repository).expanduser().resolve(strict=True)
        if not root.is_dir():
            msg = f"Repository path is not a directory: {root}"
            raise NotADirectoryError(msg)
        return root

    @staticmethod
    def _cache_path(root: Path) -> Path:
        return root / _CACHE_DIRECTORY / _CACHE_FILENAME

    @staticmethod
    def _read_payload(path: Path) -> _CacheEnvelope | None:
        try:
            raw: Any = json.loads(path.read_text(encoding="utf-8"))
            return _CacheEnvelope.model_validate(raw)
        except (OSError, ValueError):
            return None

    @staticmethod
    def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
        encoded = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
        descriptor, temporary_name = tempfile.mkstemp(
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
        )
        temporary_path = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "wb") as temporary_file:
                temporary_file.write(encoded)
                temporary_file.flush()
                os.fsync(temporary_file.fileno())
            os.replace(temporary_path, path)
        finally:
            try:
                temporary_path.unlink()
            except FileNotFoundError:
                pass
