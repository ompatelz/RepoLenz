"""Structured repository-discovery results, independent from CLI rendering."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class RepositoryScan(BaseModel):
    """Static inventory of a repository discovered without executing its code."""

    model_config = ConfigDict(frozen=True)

    root: str
    name: str
    files: list[str] = Field(default_factory=list)
    directories: list[str] = Field(default_factory=list)
    python_files: list[str] = Field(default_factory=list)
    packages: list[str] = Field(default_factory=list)
    tests: list[str] = Field(default_factory=list)
    source_directories: list[str] = Field(default_factory=list)
    dependency_manifests: list[str] = Field(default_factory=list)
    configuration_files: list[str] = Field(default_factory=list)
    entrypoints: list[str] = Field(default_factory=list)
    readme: str | None = None
    gitignore: str | None = None

    @property
    def file_count(self) -> int:
        return len(self.files)

    @property
    def directory_count(self) -> int:
        return len(self.directories)
