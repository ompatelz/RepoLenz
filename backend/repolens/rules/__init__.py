"""Architecture rules, boundaries, and static invariant checking."""

from __future__ import annotations

from repolens.rules.engine import ArchitectureRuleEngine, load_rules
from repolens.rules.models import (
    ArchitectureRulesConfig,
    LayerBoundaryRule,
    RuleCheckReport,
    RuleSeverity,
    RuleViolation,
)

__all__ = [
    "ArchitectureRuleEngine",
    "ArchitectureRulesConfig",
    "LayerBoundaryRule",
    "RuleCheckReport",
    "RuleSeverity",
    "RuleViolation",
    "load_rules",
]
