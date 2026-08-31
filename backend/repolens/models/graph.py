"""Extensible graph contracts shared by scanners, parsers, and renderers."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class NodeType(StrEnum):
    REPOSITORY = "repository"
    PACKAGE = "package"
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    ROUTE = "route"
    MODEL = "model"
    DEPENDENCY = "dependency"


class EdgeType(StrEnum):
    CONTAINS = "contains"
    IMPORTS = "imports"
    CALLS = "calls"
    INHERITS = "inherits"
    EXPOSES = "exposes"
    USES = "uses"
    DEPENDS_ON = "depends_on"


class Node(BaseModel):
    """A source or conceptual item in an architecture graph."""

    model_config = ConfigDict(frozen=True)

    id: str
    type: NodeType
    name: str
    path: str | None = None
    line_start: int | None = Field(default=None, ge=1)
    line_end: int | None = Field(default=None, ge=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Edge(BaseModel):
    """A directed, evidence-backed relationship between graph nodes."""

    model_config = ConfigDict(frozen=True)

    source: str
    target: str
    type: EdgeType
    metadata: dict[str, Any] = Field(default_factory=dict)


class GraphDocument(BaseModel):
    """Versioned, JSON-serializable contract for architecture consumers."""

    schema_version: str = "1"
    metadata: dict[str, Any] = Field(default_factory=dict)
    nodes: list[Node] = Field(default_factory=list)
    edges: list[Edge] = Field(default_factory=list)
    stats: dict[str, int | float | str] = Field(default_factory=dict)
    insights: dict[str, Any] = Field(default_factory=dict)
