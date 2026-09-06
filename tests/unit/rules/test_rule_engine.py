from repolens.graph.engine import GraphEngine
from repolens.models.graph import Edge, EdgeType, GraphDocument, Node, NodeType
from repolens.rules.engine import ArchitectureRuleEngine
from repolens.rules.models import (
    ArchitectureRulesConfig,
    LayerBoundaryRule,
    RuleSeverity,
)


def test_rule_engine_passes_clean_graph() -> None:
    doc = GraphDocument(
        nodes=[
            Node(id="module:core", type=NodeType.MODULE, name="core"),
            Node(id="module:api", type=NodeType.MODULE, name="api"),
        ],
        edges=[
            Edge(source="module:api", target="module:core", type=EdgeType.IMPORTS),
        ],
    )
    engine = ArchitectureRuleEngine()
    report = engine.check(GraphEngine(doc))
    assert report.passed
    assert report.violations_count == 0


def test_rule_engine_detects_layer_violations() -> None:
    doc = GraphDocument(
        nodes=[
            Node(id="module:core.db", type=NodeType.MODULE, name="core.db", path="core/db.py"),
            Node(
                id="module:api.users", type=NodeType.MODULE, name="api.users", path="api/users.py"
            ),
        ],
        edges=[
            # Core illegally imports API
            Edge(source="module:core.db", target="module:api.users", type=EdgeType.IMPORTS),
        ],
    )
    config = ArchitectureRulesConfig(
        layer_boundaries=[
            LayerBoundaryRule(
                source_pattern="core.*",
                forbidden_target_pattern="api.*",
                description="Core must not depend on API presentation layer",
                severity=RuleSeverity.ERROR,
            )
        ]
    )
    engine = ArchitectureRuleEngine(config)
    report = engine.check(GraphEngine(doc))

    assert not report.passed
    assert report.violations_count == 1
    assert report.error_count == 1
    assert report.violations[0].rule_id == "layer-boundary"
    assert "Core must not depend on API presentation layer" in report.violations[0].message


def test_rule_engine_detects_cycles() -> None:
    doc = GraphDocument(
        nodes=[
            Node(id="module:a", type=NodeType.MODULE, name="a"),
            Node(id="module:b", type=NodeType.MODULE, name="b"),
        ],
        edges=[
            Edge(source="module:a", target="module:b", type=EdgeType.IMPORTS),
            Edge(source="module:b", target="module:a", type=EdgeType.IMPORTS),
        ],
    )
    config = ArchitectureRulesConfig(allow_cycles=False)
    engine = ArchitectureRuleEngine(config)
    report = engine.check(GraphEngine(doc))

    assert not report.passed
    assert any(v.rule_id == "no-cycles" for v in report.violations)


def test_rule_engine_max_fan_out() -> None:
    doc = GraphDocument(
        nodes=[
            Node(id="module:god", type=NodeType.MODULE, name="god"),
            Node(id="module:d1", type=NodeType.MODULE, name="d1"),
            Node(id="module:d2", type=NodeType.MODULE, name="d2"),
            Node(id="module:d3", type=NodeType.MODULE, name="d3"),
        ],
        edges=[
            Edge(source="module:god", target="module:d1", type=EdgeType.IMPORTS),
            Edge(source="module:god", target="module:d2", type=EdgeType.IMPORTS),
            Edge(source="module:god", target="module:d3", type=EdgeType.IMPORTS),
        ],
    )
    config = ArchitectureRulesConfig(max_fan_out=2)
    engine = ArchitectureRuleEngine(config)
    report = engine.check(GraphEngine(doc))

    assert report.passed  # Warning does not fail unless strict
    assert report.warning_count == 1
    assert report.violations[0].rule_id == "max-fan-out"
