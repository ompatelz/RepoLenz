"""Language-neutral static-analysis contracts."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SymbolKind(StrEnum):
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"


class ImportKind(StrEnum):
    INTERNAL = "internal"
    STANDARD_LIBRARY = "standard_library"
    THIRD_PARTY = "third_party"
    UNRESOLVED = "unresolved"


class Symbol(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str
    kind: SymbolKind
    name: str
    module: str
    line_start: int
    line_end: int
    signature: str | None = None
    docstring: str | None = None
    decorators: list[str] = Field(default_factory=list)
    bases: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Import(BaseModel):
    model_config = ConfigDict(frozen=True)
    module: str
    name: str | None = None
    alias: str | None = None
    level: int = 0
    kind: ImportKind = ImportKind.UNRESOLVED
    line: int


class Relationship(BaseModel):
    model_config = ConfigDict(frozen=True)
    source: str
    target: str
    type: str
    line: int


class ModuleAnalysis(BaseModel):
    model_config = ConfigDict(frozen=True)
    path: str
    module: str
    symbols: list[Symbol] = Field(default_factory=list)
    imports: list[Import] = Field(default_factory=list)
    relationships: list[Relationship] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
