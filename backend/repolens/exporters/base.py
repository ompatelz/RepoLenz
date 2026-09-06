"""Base protocol for architecture graph exporters."""

from __future__ import annotations

from typing import Protocol

from repolens.graph.engine import GraphEngine


class BaseExporter(Protocol):
    """Protocol implemented by all architecture exporters."""

    def export(self, graph: GraphEngine) -> str:
        """Export the graph into the target representation format."""
        ...
