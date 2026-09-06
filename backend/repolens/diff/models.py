"""Data models for architectural graph diffing and evolution tracking."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from repolens.models.graph import NodeType


class DiffStatus(StrEnum):
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"


class NodeDiff(BaseModel):
    """Difference record for an individual architecture node."""

    model_config = ConfigDict(frozen=True)

    node_id: str
    name: str
    type: NodeType
    status: DiffStatus
    details: dict[str, Any] = Field(default_factory=dict)


class EdgeDiff(BaseModel):
    """Difference record for a directed architecture edge."""

    model_config = ConfigDict(frozen=True)

    source: str
    target: str
    type: str
    status: DiffStatus


class GraphDiffReport(BaseModel):
    """Comprehensive architecture evolution and regression report."""

    model_config = ConfigDict(frozen=True)

    base_repository: str
    target_repository: str
    added_nodes: list[NodeDiff] = Field(default_factory=list)
    removed_nodes: list[NodeDiff] = Field(default_factory=list)
    added_edges: list[EdgeDiff] = Field(default_factory=list)
    removed_edges: list[EdgeDiff] = Field(default_factory=list)
    new_cycles: list[list[str]] = Field(default_factory=list)
    broken_routes: list[str] = Field(default_factory=list)
    has_breaking_changes: bool = False
    summary: str
