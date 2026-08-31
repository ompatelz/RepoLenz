"""Application configuration with safe, explicit defaults."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Settings:
    """Runtime settings that do not depend on the analyzed repository."""

    cache_directory_name: str = ".repolens"

    def cache_path_for(self, repository: Path) -> Path:
        return repository / self.cache_directory_name
