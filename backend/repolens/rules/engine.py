"""Engine for evaluating architecture invariants and layer boundaries."""

from __future__ import annotations

import json
from pathlib import Path

from repolens.graph.engine import GraphEngine
from repolens.models.graph import EdgeType
from repolens.rules.models import (
    ArchitectureRulesConfig,
    RuleCheckReport,
    RuleSeverity,
    RuleViolation,
)


class ArchitectureRuleEngine:
    """Evaluates architecture graphs against configurable structural rules."""

    def __init__(self, config: ArchitectureRulesConfig | None = None) -> None:
        self.config = config or ArchitectureRulesConfig()

    def check(self, graph: GraphEngine) -> RuleCheckReport:
        violations: list[RuleViolation] = []

        # 1. Check for Dependency Cycles
        if not self.config.allow_cycles:
            detected_cycles = graph.cycles()
            for cycle in detected_cycles:
                cycle_str = " -> ".join(cycle)
                violations.append(
                    RuleViolation(
                        rule_id="no-cycles",
                        severity=RuleSeverity.ERROR,
                        message=f"Dependency cycle detected: {cycle_str}",
                        source_node=cycle[0],
                        target_node=cycle[1] if len(cycle) > 1 else None,
                    )
                )

        # 2. Check Layer Boundaries
        if self.config.layer_boundaries:
            for edge in graph.document.edges:
                if edge.type not in (EdgeType.IMPORTS, EdgeType.DEPENDS_ON, EdgeType.CALLS):
                    continue

                source_node = graph.node(edge.source)
                target_node = graph.node(edge.target)
                if not source_node or not target_node:
                    continue

                for rule in self.config.layer_boundaries:
                    # Match on name, id, or relative path
                    src_match = (
                        rule.matches_source(source_node.name)
                        or rule.matches_source(source_node.id)
                        or (source_node.path and rule.matches_source(source_node.path))
                    )
                    tgt_match = (
                        rule.matches_target(target_node.name)
                        or rule.matches_target(target_node.id)
                        or (target_node.path and rule.matches_target(target_node.path))
                    )

                    if src_match and tgt_match:
                        violations.append(
                            RuleViolation(
                                rule_id="layer-boundary",
                                severity=rule.severity,
                                message=(
                                    f"{rule.description}: '{source_node.name}' "
                                    f"imports forbidden target '{target_node.name}'"
                                ),
                                source_node=source_node.id,
                                target_node=target_node.id,
                                path=source_node.path,
                                line=source_node.line_start,
                            )
                        )

        # 3. Check Maximum Fan-Out
        if self.config.max_fan_out is not None:
            for node in graph.document.nodes:
                outgoing = [e for e in graph.document.edges if e.source == node.id]
                if len(outgoing) > self.config.max_fan_out:
                    violations.append(
                        RuleViolation(
                            rule_id="max-fan-out",
                            severity=RuleSeverity.WARNING,
                            message=(
                                f"Node '{node.name}' exceeds maximum allowed fan-out "
                                f"({len(outgoing)} > {self.config.max_fan_out})"
                            ),
                            source_node=node.id,
                            path=node.path,
                            line=node.line_start,
                        )
                    )

        error_count = sum(1 for v in violations if v.severity == RuleSeverity.ERROR)
        warning_count = sum(1 for v in violations if v.severity == RuleSeverity.WARNING)
        passed = error_count == 0

        summary = (
            f"Architecture check {'PASSED' if passed else 'FAILED'}: "
            f"{len(violations)} violation(s) ({error_count} errors, {warning_count} warnings)."
        )

        return RuleCheckReport(
            passed=passed,
            violations_count=len(violations),
            error_count=error_count,
            warning_count=warning_count,
            violations=violations,
            summary=summary,
        )


def load_rules(
    rules_path: Path | None = None, repo_root: Path | None = None
) -> ArchitectureRulesConfig:
    """Load architecture rules from a path or standard repository location."""
    candidate_paths: list[Path] = []
    if rules_path:
        candidate_paths.append(rules_path)
    elif repo_root:
        candidate_paths.extend(
            [
                repo_root / ".repolens" / "rules.json",
                repo_root / "architecture_rules.json",
            ]
        )

    for target in candidate_paths:
        if target.is_file():
            try:
                data = json.loads(target.read_text(encoding="utf-8"))
                return ArchitectureRulesConfig.model_validate(data)
            except Exception:
                pass

    return ArchitectureRulesConfig()
