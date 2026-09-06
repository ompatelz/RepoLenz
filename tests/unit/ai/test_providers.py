import pytest

from repolens.ai.models import NodeExplanationContext
from repolens.ai.providers import (
    MockExplanationProvider,
    OfflineExplanationProvider,
    OpenAICompatibleProvider,
    get_provider,
)
from repolens.models.graph import Edge, EdgeType, Node, NodeType


def test_offline_explanation_provider_generates_insights() -> None:
    context = NodeExplanationContext(
        node=Node(
            id="module:core.db",
            type=NodeType.MODULE,
            name="core.db",
            path="core/db.py",
            line_start=1,
            line_end=50,
        ),
        neighbors=[
            Node(id="module:api.users", type=NodeType.MODULE, name="api.users"),
            Node(id="module:api.orders", type=NodeType.MODULE, name="api.orders"),
            Node(id="module:api.billing", type=NodeType.MODULE, name="api.billing"),
            Node(id="module:api.auth", type=NodeType.MODULE, name="api.auth"),
        ],
        incoming_edges=[
            Edge(source="module:api.users", target="module:core.db", type=EdgeType.IMPORTS),
            Edge(source="module:api.orders", target="module:core.db", type=EdgeType.IMPORTS),
            Edge(source="module:api.billing", target="module:core.db", type=EdgeType.IMPORTS),
            Edge(source="module:api.auth", target="module:core.db", type=EdgeType.IMPORTS),
        ],
        outgoing_edges=[],
        source_snippet="class DatabaseConnection:\n    pass",
        repository_name="test_repo",
    )

    provider = OfflineExplanationProvider()
    explanation = provider.explain(context)

    assert explanation.node_id == "module:core.db"
    assert explanation.provider == "offline"
    assert "core.db" in explanation.summary
    assert "Core Shared Dependency" in explanation.role
    assert "depend directly on this node" in explanation.architectural_impact
    assert len(explanation.recommendations) > 0


def test_mock_explanation_provider() -> None:
    context = NodeExplanationContext(node=Node(id="route:index", type=NodeType.ROUTE, name="GET /"))
    provider = MockExplanationProvider()
    explanation = provider.explain(context)
    assert explanation.provider == "mock"
    assert explanation.node_id == "route:index"
    assert "Mock" in explanation.summary


def test_openai_provider_missing_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("REPOLENS_AI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="requires an API key"):
        OpenAICompatibleProvider()


def test_get_provider_factory() -> None:
    assert isinstance(get_provider("offline"), OfflineExplanationProvider)
    assert isinstance(get_provider("mock"), MockExplanationProvider)
    with pytest.raises(ValueError, match="Unknown explanation provider"):
        get_provider("invalid_provider_name")
