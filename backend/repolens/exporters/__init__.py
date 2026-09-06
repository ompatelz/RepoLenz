"""Architecture diagram and report exporters."""

from __future__ import annotations

from repolens.exporters.base import BaseExporter
from repolens.exporters.dot import DotExporter
from repolens.exporters.html import HtmlReportExporter
from repolens.exporters.mermaid import MermaidExporter
from repolens.exporters.plantuml import PlantUmlExporter

__all__ = [
    "BaseExporter",
    "DotExporter",
    "HtmlReportExporter",
    "MermaidExporter",
    "PlantUmlExporter",
    "get_exporter",
]


def get_exporter(format_name: str) -> BaseExporter:
    """Return an exporter instance for the given format."""
    normalized = format_name.lower().strip()
    if normalized in ("mermaid", "mmd"):
        return MermaidExporter()
    if normalized in ("plantuml", "puml"):
        return PlantUmlExporter()
    if normalized in ("dot", "graphviz"):
        return DotExporter()
    if normalized in ("html", "report"):
        return HtmlReportExporter()
    raise ValueError(
        f"Unsupported export format '{format_name}'. "
        "Supported formats: mermaid, plantuml, dot, html."
    )
