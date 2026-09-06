"""Optional AI and static architectural explanation subsystem."""

from __future__ import annotations

from repolens.ai.context import build_node_context, extract_bounded_snippet
from repolens.ai.models import NodeExplanation, NodeExplanationContext
from repolens.ai.providers import (
    BaseExplanationProvider,
    MockExplanationProvider,
    OfflineExplanationProvider,
    OpenAICompatibleProvider,
    get_provider,
)

__all__ = [
    "BaseExplanationProvider",
    "MockExplanationProvider",
    "NodeExplanation",
    "NodeExplanationContext",
    "OfflineExplanationProvider",
    "OpenAICompatibleProvider",
    "build_node_context",
    "extract_bounded_snippet",
    "get_provider",
]
