"""Data models for architectural rules and boundary verification."""

from __future__ import annotations

from enum import StrEnum
from fnmatch import fnmatch

from pydantic import BaseModel, ConfigDict, Field


class RuleSeverity(StrEnum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class LayerBoundaryRule(BaseModel):
    """Disallows dependencies from source packages/modules into forbidden target patterns."""

    model_config = ConfigDict(frozen=True)

    source_pattern: str
    forbidden_target_pattern: str
    description: str = "Layer boundary violation"
    severity: RuleSeverity = RuleSeverity.ERROR

    def matches_source(self, name: str) -> bool:
        return fnmatch(name, self.source_pattern)

    def matches_target(self, name: str) -> bool:
        return fnmatch(name, self.forbidden_target_pattern)


class ArchitectureRulesConfig(BaseModel):
    """Configuration for repository architecture verification."""

    model_config = ConfigDict(frozen=True)

    allow_cycles: bool = False
    max_fan_out: int | None = None
    layer_boundaries: list[LayerBoundaryRule] = Field(default_factory=list)


class RuleViolation(BaseModel):
    """Record of an architectural invariant violation."""

    model_config = ConfigDict(frozen=True)

    rule_id: str
    severity: RuleSeverity
    message: str
    source_node: str
    target_node: str | None = None
    path: str | None = None
    line: int | None = None


class RuleCheckReport(BaseModel):
    """Aggregated architecture verification result."""

    model_config = ConfigDict(frozen=True)

    passed: bool
    violations_count: int
    error_count: int
    warning_count: int
    violations: list[RuleViolation] = Field(default_factory=list)
    summary: str
