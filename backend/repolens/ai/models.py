"""Data models for bounded architecture explanations."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from repolens.models.graph import Edge, Node


class NodeExplanationContext(BaseModel):
    """Strictly bounded context extracted for an architectural node explanation.

    Never includes entire codebase files or unconstrained source trees.
    """

    model_config = ConfigDict(frozen=True)

    node: Node
    neighbors: list[Node] = Field(default_factory=list)
    incoming_edges: list[Edge] = Field(default_factory=list)
    outgoing_edges: list[Edge] = Field(default_factory=list)
    source_snippet: str | None = None
    repository_name: str = "Repository"
    framework_routes: list[dict[str, Any]] = Field(default_factory=list)
    framework_models: list[dict[str, Any]] = Field(default_factory=list)


class NodeExplanation(BaseModel):
    """Structured architectural explanation for a single node."""

    model_config = ConfigDict(frozen=True)

    node_id: str
    provider: str
    summary: str
    role: str
    architectural_impact: str
    dependencies_summary: str
    recommendations: list[str] = Field(default_factory=list)
