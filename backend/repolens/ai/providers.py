"""Provider abstraction for architectural node explanations."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Protocol

from repolens.ai.models import NodeExplanation, NodeExplanationContext
from repolens.models.graph import EdgeType, NodeType


class BaseExplanationProvider(Protocol):
    """Protocol for architecture explanation providers."""

    def explain(self, context: NodeExplanationContext) -> NodeExplanation:
        """Generate a structured architecture explanation for the provided context."""
        ...


class OfflineExplanationProvider:
    """Deterministic, local-first rule-based architecture synthesizer.

    Requires no API keys, no network access, and guarantees zero external leakage.
    Produces high-fidelity structural insights grounded in static evidence.
    """

    def explain(self, context: NodeExplanationContext) -> NodeExplanation:
        node = context.node
        incoming = context.incoming_edges
        outgoing = context.outgoing_edges

        fan_in = len(incoming)
        fan_out = len(outgoing)

        incoming_import_count = sum(1 for e in incoming if e.type == EdgeType.IMPORTS)
        outgoing_import_count = sum(1 for e in outgoing if e.type == EdgeType.IMPORTS)
        route_links = sum(1 for e in outgoing if e.type == EdgeType.EXPOSES)

        # 1. Determine Architectural Role
        role: str
        if node.type == NodeType.ROUTE or context.framework_routes:
            method = node.metadata.get("method", "HTTP")
            path = node.metadata.get("path", node.name)
            role = f"HTTP API Route ({method} {path})"
        elif node.type == NodeType.MODEL or context.framework_models:
            table = node.metadata.get("table_name", node.name)
            role = f"Domain Data Model (Table: {table})"
        elif node.type == NodeType.COMPONENT:
            role = "Frontend Component"
        elif node.type == NodeType.PACKAGE:
            role = "Architecture Package Namespace"
        elif fan_in >= 4 and fan_out <= 2:
            role = "Core Shared Dependency (High Fan-In)"
        elif fan_out >= 4 and fan_in <= 1:
            role = "High-Level Orchestrator (High Fan-Out)"
        elif fan_in == 0 and fan_out > 0:
            role = "Top-Level Entry Point / Coordinator"
        elif fan_in > 0 and fan_out == 0:
            role = "Leaf Implementation / Utility"
        else:
            role = f"Domain {node.type.value.title()}"

        # 2. Synthesize Summary
        if node.path and node.line_start:
            loc = f" at {node.path}:{node.line_start}"
        elif node.path:
            loc = f" in {node.path}"
        else:
            loc = ""
        summary = (
            f"`{node.name}` is a {node.type.value}{loc}. "
            f"Referenced by {fan_in} connection(s), references {fan_out} element(s)."
        )

        # 3. Architectural Impact
        impact_points: list[str] = []
        if fan_in >= 4:
            impact_points.append(
                f"Critical hub: {fan_in} components depend directly on this node. "
                "Modifying its signature risks broad ripple effects across dependents."
            )

        elif fan_in == 0:
            impact_points.append(
                "Zero incoming dependencies detected. "
                "This may be an entrypoint, dynamically loaded, or candidate for pruning."
            )
        else:
            impact_points.append(
                f"Moderate coupling: {fan_in} dependent(s) rely on this interface."
            )

        if fan_out > 6:
            impact_points.append(
                f"High outward coupling: connects to {fan_out} downstream elements. "
                "Consider decomposing responsibilities."
            )

        if context.framework_routes:
            impact_points.append("Exposes public API surface evidenced by framework routes.")
        if context.framework_models:
            impact_points.append("Governs persistent database schema and entity constraints.")

        architectural_impact = " ".join(impact_points)

        # 4. Dependencies Summary
        deps_summary_parts: list[str] = []
        if incoming_import_count > 0:
            deps_summary_parts.append(f"Imported by {incoming_import_count} module(s)")
        if outgoing_import_count > 0:
            deps_summary_parts.append(f"imports {outgoing_import_count} module(s)")
        if route_links > 0:
            deps_summary_parts.append(f"exposes {route_links} route handler(s)")

        if deps_summary_parts:
            dependencies_summary = f"Direct relations: {', '.join(deps_summary_parts)}."
        else:
            dependencies_summary = "Isolated or self-contained relative to internal dependencies."

        # 5. Actionable Recommendations
        recommendations: list[str] = []
        if fan_in >= 4:
            recommendations.append(
                "Maintain strict backward compatibility and unit tests to protect dependents."
            )
        if fan_out >= 6:
            recommendations.append(
                "Evaluate Single Responsibility Principle (SRP) to reduce outward fan-out."
            )
        if fan_in == 0 and node.type in (NodeType.CLASS, NodeType.FUNCTION, NodeType.MODULE):
            recommendations.append(
                "Audit whether this component is a CLI entrypoint or dead code candidate."
            )
        if node.type == NodeType.ROUTE and not node.metadata.get("response_model"):
            recommendations.append(
                "Define an explicit response model contract for schema consistency."
            )
        if not recommendations:
            recommendations.append(
                "Interface has balanced coupling and standard locality within its module."
            )

        return NodeExplanation(
            node_id=node.id,
            provider="offline",
            summary=summary,
            role=role,
            architectural_impact=architectural_impact,
            dependencies_summary=dependencies_summary,
            recommendations=recommendations,
        )


class MockExplanationProvider:
    """Deterministic mock provider for automated unit and integration tests."""

    def explain(self, context: NodeExplanationContext) -> NodeExplanation:
        return NodeExplanation(
            node_id=context.node.id,
            provider="mock",
            summary=f"Mock explanation for {context.node.name}",
            role="Mock Architectural Role",
            architectural_impact="Mock architectural impact assessment.",
            dependencies_summary="Mock dependencies summary.",
            recommendations=["Mock recommendation 1", "Mock recommendation 2"],
        )


class OpenAICompatibleProvider:
    """Optional explanation provider using an OpenAI-compatible HTTP endpoint.

    Uses standard library urllib without external heavy dependencies.
    Configurable via:
    - REPOLENS_AI_API_KEY (or OPENAI_API_KEY)
    - REPOLENS_AI_BASE_URL (defaults to https://api.openai.com/v1)
    - REPOLENS_AI_MODEL (defaults to gpt-4o-mini)
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float = 15.0,
    ) -> None:
        self.api_key = api_key or os.getenv("REPOLENS_AI_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.base_url = (
            base_url or os.getenv("REPOLENS_AI_BASE_URL") or "https://api.openai.com/v1"
        ).rstrip("/")
        self.model = model or os.getenv("REPOLENS_AI_MODEL") or "gpt-4o-mini"
        self.timeout = timeout

        if not self.api_key:
            raise ValueError(
                "AI provider requires an API key. Set REPOLENS_AI_API_KEY or OPENAI_API_KEY."
            )

    def explain(self, context: NodeExplanationContext) -> NodeExplanation:
        prompt_payload = {
            "node": {
                "id": context.node.id,
                "name": context.node.name,
                "type": context.node.type.value,
                "path": context.node.path,
                "metadata": context.node.metadata,
            },
            "incoming_edges": [
                {"source": e.source, "type": e.type.value, "metadata": e.metadata}
                for e in context.incoming_edges
            ],
            "outgoing_edges": [
                {"target": e.target, "type": e.type.value, "metadata": e.metadata}
                for e in context.outgoing_edges
            ],
            "framework_routes": context.framework_routes,
            "framework_models": context.framework_models,
            "bounded_source_snippet": context.source_snippet,
        }

        system_instruction = (
            "You are RepoLens Architectural AI. Analyze the strictly bounded context. "
            "Never hallucinate outside given facts. Respond strictly with JSON:\n"
            "{\n"
            '  "summary": "Concise 1-2 sentence description",\n'
            '  "role": "Architectural classification in 2-5 words",\n'
            '  "architectural_impact": "Analysis of coupling and stability",\n'
            '  "dependencies_summary": "Summary of dependencies",\n'
            '  "recommendations": ["Recommendation 1", "Recommendation 2"]\n'
            "}"
        )

        request_body = json.dumps(
            {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": json.dumps(prompt_payload)},
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.2,
            }
        ).encode("utf-8")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        endpoint = f"{self.base_url}/chat/completions"
        req = urllib.request.Request(endpoint, data=request_body, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))
            content_str = resp_data["choices"][0]["message"]["content"]
            parsed = json.loads(content_str)
            return NodeExplanation(
                node_id=context.node.id,
                provider="openai",
                summary=parsed.get("summary", f"Architecture summary for {context.node.name}"),
                role=parsed.get("role", "Architectural Element"),
                architectural_impact=parsed.get(
                    "architectural_impact", "Coupling within expected parameters."
                ),
                dependencies_summary=parsed.get(
                    "dependencies_summary", "Standard bounded dependencies."
                ),
                recommendations=parsed.get("recommendations", []),
            )
        except Exception as err:
            raise RuntimeError(f"OpenAI provider request failed: {err}") from err


def get_provider(name: str | None = None) -> BaseExplanationProvider:
    """Return an explanation provider instance based on name or environment."""
    provider_name = (name or os.getenv("REPOLENS_AI_PROVIDER") or "offline").lower().strip()

    if provider_name == "mock":
        return MockExplanationProvider()
    if provider_name in ("openai", "llm"):
        return OpenAICompatibleProvider()
    if provider_name == "offline":
        return OfflineExplanationProvider()

    raise ValueError(
        f"Unknown explanation provider '{provider_name}'. "
        "Supported providers: 'offline', 'openai', 'mock'."
    )
