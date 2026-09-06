"""Normalized parser interface for static analysis across languages."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from repolens.parsers.models import ModuleAnalysis


@runtime_checkable
class BaseParser(Protocol):
    """Protocol for language-specific static analysis parsers."""

    def parse_file(self, path: Path | str, module_path: str | None = None) -> ModuleAnalysis:
        """Parse source file statically and extract symbols, imports, and relationships."""
        ...
